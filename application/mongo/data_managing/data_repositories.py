from __future__ import annotations

from application.resources import TBoolExc, TDesc
from application.database import *
from .base import *


class MongoDataRepositoryMetadata(MongoBaseMetadata):
    pass


@BaseDataRepository.set_class
class MongoDataRepository(MongoBaseDataRepository):

    # 1. Fields
    meta = {
        'indexes': [
            {'fields': ('workspace', 'name'), 'unique': True},
        ]
    }

    workspace = db.ReferenceField(MongoBaseWorkspace)               # workspace
    name = db.StringField(required=True)                            # repo name
    root = db.StringField(required=True)                            # repo root directory
    metadata = db.EmbeddedDocumentField(MongoDataRepositoryMetadata)
    files = db.MapField(db.IntField())                              # relative_path => file

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
    def create(cls, name: str, workspace: MongoBaseWorkspace, root: str = None,
               save: bool = True, parent_locked=False) -> MongoBaseDataRepository | None:

        # TODO Validation!
        if root is None:
            root = f"DataRepository_{name}"

        owner = workspace.get_owner()

        with owner.sub_resource_create(locked=parent_locked):
            with workspace.sub_resource_create(locked=parent_locked):

                now = datetime.utcnow()
                # noinspection PyArgumentList
                repository = cls(
                    workspace=workspace,
                    name=name,
                    root=root,
                    metadata=MongoDataRepositoryMetadata(created=now, last_modified=now),
                    files={},
                )
                if repository is not None:
                    with repository.resource_create():
                        if save:
                            repository.save(create=True)
                            print(f"Created DataRepository '{name}' with id '{repository.id}'.")

                        manager = User.get_data_manager()
                        repository.root = repository.data_repo_base_dir()
                        repository.save()
                        manager.create_subdir(
                            repository.get_root(),
                            parents=[
                                owner.user_base_dir(),
                                workspace.workspace_base_dir(),
                            ]
                        )
                return repository

    # 5. Delete + callbacks
    def delete(self, locked=False, parent_locked=False) -> TBoolExc:

        owner = self.get_owner()
        workspace = self.get_workspace()

        with owner.sub_resource_delete(locked=parent_locked):
            with workspace.sub_resource_delete(locked=parent_locked):
                with self.resource_delete(locked=locked):
                    # TODO Check sub-repositories!
                    try:
                        db.Document.delete(self)
                        manager = User.get_data_manager()
                        parents = [
                            owner.user_base_dir(),
                            workspace.workspace_base_dir(),
                        ]
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

    def get_workspace(self) -> MongoBaseWorkspace:
        return self.workspace

    def get_owner(self) -> MongoBaseUser:
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
            'metadata': self.metadata.to_dict(),
        }

    # 7. Query-like instance methods
    # 8. Status methods

    # 9. Special methods