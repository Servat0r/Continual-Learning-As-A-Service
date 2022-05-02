from __future__ import annotations
from datetime import datetime

from application.database import *
from application.resources import TBoolExc, TDesc, t, UserWorkspaceResourceContext
from application.models import User, Workspace
from application.data_managing import BaseDataRepository, BaseDataSubRepository
from application.mongo.mongo_base_metadata import MongoBaseMetadata


class MongoDataRepositoryMetadata(MongoBaseMetadata):
    pass


@BaseDataRepository.set_class
class MongoDataRepository(BaseDataRepository, db.Document):

    # 1. Fields
    meta = {
        'indexes': [
            {'fields': ('workspace', 'name'), 'unique': True}
        ]
    }

    workspace = db.ReferenceField(Workspace.get_class())            # workspace
    name = db.StringField(required=True)                            # repo name
    root = db.StringField(required=True)                            # repo root directory
    metadata = db.EmbeddedDocumentField(MongoDataRepositoryMetadata)

    # 2. Uri methods
    @classmethod
    def get_by_uri(cls, uri: str):
        s = uri.split(cls.uri_separator())
        username = s[1]
        wname = s[2]
        name = s[3]
        workspace = Workspace.canonicalize((username, wname))
        return cls.objects(workspace=workspace, name=name).first()

    @property
    def uri(self):
        context = UserWorkspaceResourceContext(self.get_owner().get_name(), self.get_workspace().get_name())
        return self.dfl_uri_builder(context, self.get_name())

    # 3. General classmethods
    @classmethod
    def get(cls, workspace: Workspace = None, name: str = None) -> list[BaseDataRepository]:
        args = {}
        if workspace is not None:
            args['workspace'] = workspace
        if name is not None:
            args['name'] = name
        return list(cls.objects(**args).all())

    # 4. Create + callbacks
    @classmethod
    def before_create(cls, name: str, workspace: Workspace) -> TBoolExc:
        return True, None

    @classmethod
    def after_create(cls, repository: BaseDataRepository) -> TBoolExc:
        repository.root = repository.data_repo_base_dir()
        repository.save()
        manager = Workspace.get_data_manager()
        owner = repository.get_owner()
        workspace = repository.get_workspace()
        return manager.create_subdir(
            repository.get_root(),
            parents=[
                owner.user_base_dir(),
                workspace.workspace_base_dir(),
            ]
        )

    @classmethod
    def create(cls, name: str, workspace: Workspace, root: str = None, save: bool = True) -> MongoDataRepository | None:
        # TODO Validation!
        now = datetime.utcnow()
        if root is None:
            root = f"DataRepository_{name}"
        # noinspection PyArgumentList
        repository = cls(
            workspace=workspace,
            name=name,
            root=root,
            metadata=MongoDataRepositoryMetadata(created=now, last_modified=now),
        )
        if save:
            repository.save(create=True)
            print(f"Created DataRepository '{name}' with id '{repository.id}'.")
        return repository

    # 5. Delete + callbacks
    @classmethod
    def before_delete(cls, repository: BaseDataRepository) -> TBoolExc:
        try:
            # TODO Aggiungere chiusura etc.

            return True, None
        except Exception as ex:
            return False, ex

    @classmethod
    def after_delete(cls, repository: BaseDataRepository) -> TBoolExc:
        try:
            manager = Workspace.get_data_manager()
            workspace = repository.get_workspace()
            owner = repository.get_owner()
            parents = [
                owner.user_base_dir(),
                workspace.workspace_base_dir(),
            ]
            return manager.remove_subdir(
                repository.get_root(),
                parents=parents,
            )
        except Exception as ex:
            return False, ex

    @classmethod
    def delete(cls, repository: BaseDataRepository) -> TBoolExc:
        try:
            # TODO Controlli!
            db.Document.delete(repository)
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

    def get_workspace(self) -> Workspace:
        return self.workspace

    def get_owner(self) -> User:
        return self.workspace.get_owner()

    def get_absolute_path(self) -> str:
        manager = Workspace.get_data_manager()
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
            'sub_repositories': [obj.to_dict() for obj in self.sub_repositories],
            'metadata': self.metadata.to_dict(),
        }

    # 7. Query-like instance methods
    def get_sub_repositories(self) -> list[BaseDataSubRepository]:
        return BaseDataSubRepository.get_by_data_repository(self)

    # 8. Status methods

    # 9. Special methods