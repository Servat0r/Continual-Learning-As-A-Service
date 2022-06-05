from __future__ import annotations

import time
import sys
from datetime import datetime

from application.utils import TBoolExc, TDesc, t
from application.database import *
from application.models import Workspace

from application.data_managing.base import BaseDataRepository, BaseDataManager, TFContent, TFContentLabel
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
    files = db.MapField(db.IntField())                              # relative_path => file

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

    # 2. Uri methods
    @classmethod
    def get_by_claas_urn(cls, urn: str):
        s = urn.split(cls.claas_urn_separator())
        username = s[1]
        wname = s[2]
        name = s[3]
        workspace = Workspace.canonicalize((username, wname))
        ls = cls.get(workspace=workspace, name=name)
        return ls[0] if len(ls) > 0 else None

    @property
    def claas_urn(self):
        context = UserWorkspaceResourceContext(self.get_owner().get_name(), self.get_workspace().get_name())
        return self.dfl_claas_urn_builder(context, self.get_name())

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
                files={},
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
    def delete(self, locked=False, parents_locked=False) -> TBoolExc:

        workspace = self.get_workspace()

        context = UserWorkspaceResourceContext(workspace.get_owner().get_name(), workspace.get_name())
        with self.resource_delete(locked=locked, parents_locked=parents_locked):
            try:
                BenchmarkClass = t.cast(ReferrableDataType, DataType.get_type('Benchmark')).config_type()
                benchmarks = BenchmarkClass.get(workspace=self.get_workspace())
                for benchmark in benchmarks:
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

    def to_dict(self) -> TDesc:
        files = {self.denormalize(k): v for k, v in self.files.items()}
        return {
            'name': self.name,
            'root': self.root,
            'workspace': self.workspace.to_dict(),
            'metadata': self.metadata.to_dict(),
            'files': files,
        }

    # 9. Special methods
    def add_directory(self, dir_name: str, parents: list[str] = None) -> TBoolExc:
        with self.resource_read():
            manager = BaseDataManager.get()
            parents = self._complete_parents(parents)
            return manager.create_subdir(dir_name, parents)

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
                    self.files = {
                        (k.replace(src_path, dest_path, 1) if k.startswith(src_path) else k): v
                        for k, v in self.files.items()
                    }
                    self.save()
                return result, exc

    def delete_directory(self, dir_name: str, dir_parents: list[str] = None) -> TBoolExc:
        manager = BaseDataManager.get()
        dir_parents = self._complete_parents(dir_parents)
        with self.resource_write():
            result, exc = manager.remove_subdir(dir_name, dir_parents)
            if result:
                dir_path = self.normalize('/'.join(dir_parents + [dir_name]))
                fcopy = self.files.copy()
                for path in fcopy.keys():
                    if path.startswith(dir_path):
                        self.files.pop(path)
                self.files = fcopy
                self.save()
            return result, exc

    def add_file(self, file_name: str, file_content, label: int,
                 parents: list[str] = None, locked=False, parents_locked=False) -> TBoolExc:
        with self.resource_write(locked, parents_locked):
            manager = BaseDataManager.get()
            complete_parents = self._complete_parents(parents)
            content: TFContent = (file_name, complete_parents, file_content)
            result, exc = manager.create_file(content)
            if result:
                file_path = self.normalize('/'.join(parents + [file_name]))
                self.files[file_path] = label
                self.save()
            return result, exc

    def add_files(self, files: t.Iterable[TFContentLabel], locked=False, parents_locked=False) -> list[str]:
        with self.resource_write(locked, parents_locked):
            created: list[str] = []

            for item in iter(files):
                file, label = item
                result, exc = self.add_file(
                    file_name=file[0], file_content=file[2], label=label,
                    parents=file[1], locked=True, parents_locked=True,
                )
                if result:
                    path = '/'.join(file[1] + [file[0]])
                    created.append(path)
                    self.files[self.normalize(path)] = label
                else:
                    print(exc)

            self.save()
            return created

    def add_archive(self, stream, labels: dict, base_path_list: list[str], archive_type='zip', locked=False,
                    parents_locked=False) -> tuple[int, list[str]]:     # total_files_retrieved, added_files
        elapsed = time.perf_counter()
        manager = BaseDataManager.get()
        with self.resource_write(locked, parents_locked):
            complete_path_list = self._complete_parents(base_path_list)
            total, created = manager.add_archive(stream, archive_type=archive_type, base_path_list=complete_path_list)
            print("Before adding labels")
            for fpath in created:
                label = int(labels.get(fpath))
                fpath = '/'.join(base_path_list + [fpath])
                self.files[self.normalize(fpath)] = label
            print("Before saving")
            self.save()
        elapsed = time.perf_counter() - elapsed
        print(f"add_archive to {'/'.join(base_path_list)} elapsed time: {elapsed} seconds", file=sys.stderr)
        return total, created

    def get_file_label(self, file_path: str,
                       locked=False, parents_locked=False) -> int:
        with self.resource_read(locked, parents_locked):
            label = self.files.get(self.normalize(file_path))
            return label

    def get_all_files(self, root_path: str, include_labels=True,
                      locked=False, parents_locked=False) -> tuple[list[str], t.Optional[list[int]]]:
        result = []
        labels = [] if include_labels else None
        root_path = self.normalize(root_path)

        with self.resource_read(locked, parents_locked):
            for item in self.files.items():
                file: str = item[0]
                label: int = item[1]
                if file.startswith(root_path):
                    result.append(self.denormalize(file))
                    if include_labels:
                        labels.append(label)

        return result, labels

    def __repr__(self):
        return f"{type(self).__name__} <id = {self.id}> [urn = {self.claas_urn}]"

    def __str__(self):
        return self.__repr__()


__all__ = [
    'MongoDataRepositoryMetadata',
    'MongoDataRepository',
]