from __future__ import annotations

import time
import sys
from datetime import datetime

from application.utils import TBoolExc, TDesc, t, TBoolStr, auto_tboolexc
from application.database import *

from application.data_managing.base import BaseDataRepository, BaseDataManager, TFContent
from application.resources.contexts import UserWorkspaceResourceContext
from application.resources.base import DataType, ReferrableDataType

from application.mongo.locking import RWLockableDocument
from application.mongo.mongo_base_metadata import MongoBaseMetadata
from application.mongo.base import MongoBaseUser, MongoBaseWorkspace

from .base import *


class MongoDataRepositoryMetadata(MongoBaseMetadata):
    pass


@BaseDataRepository.set_class
class MongoDataRepository(MongoBaseDataRepository):

    # 1. Fields
    _COLLECTION = 'data_repositories'

    meta = {
        'collection': _COLLECTION,
        'indexes': [
            {'fields': ('workspace', 'name'), 'unique': True},
        ]
    }

    workspace = db.ReferenceField(MongoBaseWorkspace)               # workspace
    name = db.StringField(required=True)                            # repo name
    description = db.StringField(default='')
    root = db.StringField(required=True)                            # repo root directory
    metadata = db.EmbeddedDocumentField(MongoDataRepositoryMetadata)
    files = db.ListField(db.StringField(), default=[])                              # relative_path => file

    def _complete_parents(self, parents: list[str] = None):
        workspace = self.get_workspace()
        return workspace.data_base_dir_parents() \
            + [
                workspace.data_base_dir(),
                self.get_root(),
            ] \
            + (parents or [])

    @property
    def parents(self) -> set[RWLockableDocument]:
        return {self.workspace}

    # 3. General classmethods
    @classmethod
    def get(cls, workspace: MongoBaseWorkspace = None, name: str = None, **kwargs) -> list[BaseDataRepository]:
        if workspace is not None:
            kwargs['workspace'] = workspace
        if name is not None:
            kwargs['name'] = name
        return list(cls.objects(**kwargs).all())

    # 4. Create + callbacks
    @classmethod
    def create(cls, name: str, workspace: MongoBaseWorkspace, root: str = None, desc: str = None,
               save: bool = True, parents_locked=False) -> MongoBaseDataRepository | None:

        if root is None:
            root = f"DataRepository_{name}"

        desc = desc if desc is not None else ''

        with workspace.sub_resource_create(locked=parents_locked):
            now = datetime.utcnow()
            # noinspection PyArgumentList
            repository = cls(
                workspace=workspace,
                name=name,
                description=desc,
                root=root,
                metadata=MongoDataRepositoryMetadata(created=now, last_modified=now),
                files=[],
            )
            if repository is not None:
                with repository.resource_create(parents_locked=True):
                    if save:
                        repository.save(create=True)
                        print(f"Created DataRepository '{name}' with id '{repository.id}'.")

                    manager = BaseDataManager.get()
                    repository.root = repository.data_repo_base_dir()
                    repository.save()
                    parents = workspace.data_base_dir_parents()
                    parents.append(workspace.data_base_dir())
                    manager.create_subdir(repository.get_root(), parents=parents)
            return repository

    # 5. Delete + callbacks
    @auto_tboolexc
    def delete(self, locked=False, parents_locked=False) -> TBoolExc:
        workspace = self.get_workspace()
        context = UserWorkspaceResourceContext(workspace.get_owner().get_name(), workspace.get_name())
        with self.resource_delete(locked=locked, parents_locked=parents_locked):
            try:
                BenchmarkClass = t.cast(ReferrableDataType, DataType.get_type('Benchmark')).config_type()
                benchmarks = BenchmarkClass.get(build_config__data_repository=self)
                for benchmark in benchmarks:
                    build_config = benchmark.build_config
                    if build_config.data_repository is not None:
                        benchmark.delete(context, parents_locked=True)

                db.Document.delete(self)
                manager = BaseDataManager.get()
                parents = workspace.data_base_dir_parents()
                parents.append(workspace.data_base_dir())
                manager.remove_subdir(self.get_root(), parents=parents)

                return True, None
            except Exception as ex:
                return False, ex

    # 6. Read/Update Instance methods
    def get_id(self):
        return self.id

    def get_root(self) -> str:
        return self.root

    def get_name(self) -> str:
        return self.name

    def get_description(self) -> str:
        return self.description

    def get_workspace(self) -> MongoBaseWorkspace:
        return self.workspace

    def get_owner(self) -> MongoBaseUser:
        return self.workspace.get_owner()

    def get_absolute_path(self) -> str:
        manager = BaseDataManager.get()
        workspace = self.get_workspace()
        owner = self.get_owner()
        dir_names = [
            owner.user_base_dir(),
            workspace.workspace_base_dir(),
            'Data',
            self.get_root(),
        ]
        return manager.get_dir_path(dir_names)

    def save(self, create=False) -> bool:
        # noinspection PyBroadException, PyUnusedLocal
        try:
            if create:
                db.Document.save(self, force_insert=True)
            else:
                db.Document.save(self, save_condition={'id': self.id})
            return True
        except Exception as ex:
            return False

    def data_repo_base_dir(self) -> str:
        return f"DataRepository_{self.get_id()}"

    def to_dict(self, links=True) -> TDesc:
        files = [self.denormalize(k) for k in self.files]
        result = {
            'name': self.name,
            'root': self.root,
            'metadata': self.metadata.to_dict(),
            'files': files,
        }
        result['metadata']['claas_urn'] = self.claas_urn
        BenchmarkClass = t.cast(ReferrableDataType, DataType.get_type('Benchmark')).config_type()
        benchmarks = list(BenchmarkClass.get(build_config__data_repository=self))
        result['benchmarks'] = [benchmark.to_dict(links=False) for benchmark in benchmarks]
        if links:
            result['links'] = {
                'owner': ('User', self.get_owner()),
                'workspace': ('Workspace', self.get_workspace()),
            }
        return result

    # noinspection PyShadowingNames
    def update_last_modified(self, time: datetime = None, save: bool = True):
        self.metadata.update_last_modified(time)
        if save:
            self.save()

    def update(self, updata: TDesc) -> TBoolStr:
        # Could update name and description
        name = updata.get('name')
        description = updata.get('description')
        to_update = (name is not None and self.name != name) or (description is not None and self.description != description)
        if to_update:
            self.name = name if name is not None else self.name
            self.description = description if description is not None else self.description
            self.update_last_modified(save=True)
            return True, None
        else:
            return True, None

    # 9. Special methods
    @auto_tboolexc
    def add_directory(self, dir_name: str, parents: list[str] = None) -> TBoolExc:
        with self.resource_read():
            manager = BaseDataManager.get()
            parents = self._complete_parents(parents)
            return manager.create_subdir(dir_name, parents)

    @auto_tboolexc
    def move_directory(self, src_name: str, dest_name: str,
                       src_parents: list[str] = None, dest_parents: list[str] = None) -> TBoolExc:
        manager = BaseDataManager.get()
        if manager.is_subpath(src_name, dest_name, src_parents, dest_parents, strict=True):
            return False, ValueError("Source path is strictly contained in destination path.")
        else:
            src_parents = self._complete_parents(src_parents)
            dest_parents = self._complete_parents(dest_parents)
            with self.resource_write():
                result, exc = manager.move_subdir(src_name, dest_name, src_parents, dest_parents)
                if result:
                    src_path = self.normalize('/'.join(src_parents + [src_name]))
                    dest_path = self.normalize('/'.join(dest_parents + [dest_name]))
                    self.files = [
                        (k.replace(src_path, dest_path, 1) if k.startswith(src_path) else k)
                        for k in self.files
                    ]
                    self.save()
                return result, exc

    @auto_tboolexc
    def rename_directory(self, path: str, new_name: str):
        old_path = path.split('/')
        old_path = [s for s in old_path if len(s) > 0]
        name = old_path[-1]
        old_path = old_path[:-1]
        old_path = self._complete_parents(old_path)
        new_path = '/'.join(old_path + [new_name])
        manager = BaseDataManager.get()
        new_files = []
        modified = False
        for i in range(len(self.files)):
            file = self.files[i]
            if file.startswith(path):
                remaining = file.split(path, 1)[1].lstrip('/')
                file = new_path + '/' + remaining
                modified = True
            new_files.append(file)
        manager.rename_directory(name, old_path, new_name)
        if modified:
            self.files = new_files
            self.update_last_modified(save=True)
        return True, None

    @auto_tboolexc
    def delete_directory(self, dir_name: str, dir_parents: list[str] = None) -> TBoolExc:
        manager = BaseDataManager.get()
        dir_parents = self._complete_parents(dir_parents)
        with self.resource_write():
            result, exc = manager.remove_subdir(dir_name, dir_parents)
            if result:
                dir_path = self.normalize('/'.join(dir_parents + [dir_name]))
                fcopy = self.files.copy()
                for path in fcopy:
                    if path.startswith(dir_path):
                        self.files.remove(path)
                self.files = fcopy
                self.save()
            return result, exc

    @auto_tboolexc
    def add_file(self, file_name: str, file_content,
                 parents: list[str] = None, locked=False, parents_locked=False, save=False) -> TBoolExc:
        with self.resource_write(locked, parents_locked):
            manager = BaseDataManager.get()
            complete_parents = self._complete_parents(parents)
            content: TFContent = (file_name, complete_parents, file_content)
            result, exc = manager.create_file(content)
            if result:
                file_path = self.normalize('/'.join(parents + [file_name]))
                self.files.append(file_path)
                if save:
                    self.update_last_modified(save=True)
            return result, exc

    def add_files(self, files: t.Iterable[TFContent], locked=False, parents_locked=False) -> list[str]:
        with self.resource_write(locked, parents_locked):
            created: list[str] = []
            for file in iter(files):
                result, exc = self.add_file(
                    file_name=file[0], file_content=file[2],
                    parents=file[1], locked=True, parents_locked=True,
                )
                if result:
                    path = '/'.join(file[1] + [file[0]])
                    created.append(path)
                    # self.files.append(self.normalize(path))   # already added by add_file(...)
                else:
                    print(exc)
            if len(created) > 0:
                self.update_last_modified(save=True)
            return created

    def add_archive(self, stream, base_path_list: list[str], archive_type='zip', locked=False,
                    parents_locked=False) -> tuple[int, list[str]]:     # total_files_retrieved, added_files
        elapsed = time.perf_counter()
        manager = BaseDataManager.get()
        with self.resource_write(locked, parents_locked):
            complete_path_list = self._complete_parents(base_path_list)
            total, created = manager.add_archive(stream, archive_type=archive_type, base_path_list=complete_path_list)
            print("Before adding labels")
            for fpath in created:
                fpath = '/'.join(base_path_list + [fpath])
                self.files.append(self.normalize(fpath))
            print("Before saving")
            self.save()
        elapsed = time.perf_counter() - elapsed
        print(f"add_archive to {'/'.join(base_path_list)} elapsed time: {elapsed} seconds", file=sys.stderr)
        return total, created

    def get_all_files(self, root_path: str, locked=False, parents_locked=False) -> list[str]:
        result = []
        root_path = self.normalize(root_path)
        with self.resource_read(locked, parents_locked):
            for file in self.files:
                if file.startswith(root_path):
                    result.append(self.denormalize(file))
        return result

    @auto_tboolexc
    def delete_file(self, file_name: str, parents: list[str], locked=False, parents_locked=False, save=False) -> TBoolExc:
        with self.resource_write(locked, parents_locked):
            manager = BaseDataManager.get()
            complete_parents = self._complete_parents(parents)
            result = manager.delete_file(file_name, complete_parents)
            if result is not None:
                file_path = self.normalize('/'.join(parents + [file_name]))
                self.files.remove(file_path)
                if save:
                    self.update_last_modified(save=True)
            return True, None

    def delete_files(self, files: t.Iterable[tuple[str, list[str]]], locked=False, parents_locked=False) -> list[str]:
        with self.resource_write(locked=locked, parents_locked=parents_locked):
            deleted: list[str] = []
            for file in iter(files):
                result, exc = self.delete_file(
                    file_name=file[0], parents=file[1],
                    locked=True, parents_locked=True,
                )
                if result:
                    path = '/'.join(file[1] + [file[0]])
                    deleted.append(path)
                else:
                    print(exc)
            if len(deleted) > 0:
                self.update_last_modified(save=True)
            return deleted

    def __repr__(self):
        return f"{type(self).__name__} <id = {self.id}> [urn = {self.claas_urn}]"

    def __str__(self):
        return self.__repr__()


__all__ = [
    'MongoDataRepositoryMetadata',
    'MongoDataRepository',
]