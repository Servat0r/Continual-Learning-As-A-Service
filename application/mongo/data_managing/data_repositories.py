from __future__ import annotations
from datetime import datetime

from application.utils import TBoolExc, TDesc, t
from application.database import *
from application.models import Workspace

from application.data_managing.base import BaseDataRepository, BaseDataManager, TFContent, TFRead
from application.resources.contexts import UserWorkspaceResourceContext
from application.resources.base import DataType, ReferrableDataType

from application.mongo.utils import RWLockableDocument
from application.mongo.mongo_base_metadata import MongoBaseMetadata
from application.mongo.base import MongoBaseUser, MongoBaseWorkspace

from .base import *


class _FilesPathsIterable(t.Iterable[TFContent]):
    def __init__(self, repository: MongoDataRepository, files: t.Iterable[TFContent]):
        self.repository = repository
        self.files = iter(files)

    def __iter__(self) -> t.Iterator[TFContent]:
        return self

    def __next__(self):
        file = next(self.files, None)
        if file:
            file[1] = self.repository._complete_parents(file[1])
            return file
        else:
            return None


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
    def get_by_uri(cls, uri: str):
        s = uri.split(cls.uri_separator())
        username = s[1]
        wname = s[2]
        name = s[3]
        workspace = Workspace.canonicalize((username, wname))
        ls = cls.get(workspace=workspace, name=name)
        return ls[0] if len(ls) > 0 else None

    @property
    def uri(self):
        context = UserWorkspaceResourceContext(self.get_owner().get_name(), self.get_workspace().get_name())
        return self.dfl_uri_builder(context, self.get_name())

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

        # TODO Validation!
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
            self.get_root(),
        ]
        return manager.get_dir_path(dir_names)

    def save(self, create=False):
        db.Document.save(self, force_insert=create)

    def data_repo_base_dir(self) -> str:
        return f"DataRepository_{self.get_id()}"

    def to_dict(self) -> TDesc:
        return {
            'name': self.name,
            'root': self.root,
            'workspace': self.workspace.to_dict(),
            'metadata': self.metadata.to_dict(),
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
                return manager.move_subdir(src_name, dest_name, src_parents, dest_parents)

    def delete_directory(self, dir_name: str, dir_parents: list[str] = None) -> TBoolExc:
        manager = BaseDataManager.get()
        dir_parents = self._complete_parents(dir_parents)
        with self.resource_write():
            return manager.remove_subdir(dir_name, dir_parents)

    def add_file(self, file_name: str, file_content,
                 parents: list[str] = None, locked=False, parents_locked=False) -> TBoolExc:
        with self.resource_read(locked, parents_locked):
            manager = BaseDataManager.get()
            parents = self._complete_parents(parents)
            content: TFContent = (file_name, parents, file_content)
            return manager.create_file(content)

    def add_files(self, files: t.Iterable[TFContent], locked=False, parents_locked=False) -> list[str]:
        with self.resource_read(locked, parents_locked):
            manager = BaseDataManager.get()
            base_dir = self._complete_parents()
            return manager.create_files(files, base_dir)


__all__ = [
    'MongoDataRepositoryMetadata',
    'MongoDataRepository',
]