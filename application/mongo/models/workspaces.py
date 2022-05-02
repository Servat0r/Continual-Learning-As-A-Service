from __future__ import annotations

from application.resources import *
from application.validation import *
from application.database import db
from application.models import User, Workspace
from application.data_managing import BaseDataRepository
from application.mongo.mongo_base_metadata import MongoBaseMetadata


class WorkspaceMetadata(MongoBaseMetadata):

    def to_dict(self) -> TDesc:
        result = super().to_dict()
        return result


@Workspace.set_class
class MongoWorkspace(Workspace, db.Document):

    # 1. Fields
    OPEN = 'OPEN'
    CLOSED = 'CLOSED'

    meta = {
        'indexes': [
            {'fields': ('owner', 'name'), 'unique': True}
        ]
    }

    owner = db.ReferenceField(User.user_class())
    name = db.StringField(max_length=WORKSPACE_EXPERIMENT_MAX_CHARS)
    status = db.StringField(max_length=8)
    metadata = db.EmbeddedDocumentField(WorkspaceMetadata)

    # 2. Uri methods
    @classmethod
    def get_by_uri(cls, uri: str):
        """
        uri is of the form "workspace::<username>::<wname>"
        :param uri:
        :return:
        """
        s = uri.split(cls.uri_separator())
        print(s)
        user = User.canonicalize(s[1])
        workspace = s[2]
        return cls.objects(owner=user, name=workspace).first()

    @property
    def uri(self):
        context = UserWorkspaceResourceContext(self.owner.get_name(), self.name)
        return self.dfl_uri_builder(context)

    # 3. General classmethods
    @classmethod
    def get(cls, owner: str | User = None, name: str = None) -> t.Sequence[Workspace]:
        args = {}
        if owner is not None:
            owner = User.canonicalize(owner)
            args['owner'] = owner
        if name is not None:
            args['name'] = name
        return list(cls.objects(**args).all())

    @classmethod
    def get_by_owner(cls, owner: str | User):
        owner = User.canonicalize(owner)
        return list(cls.objects(owner=owner).all())

    @classmethod
    def all(cls):
        return list(cls.objects({}).all())

    # 4. Create + callbacks
    @classmethod
    def before_create(cls, name: str, owner: User) -> TBoolExc:
        return True, None

    @classmethod
    def after_create(cls, workspace: Workspace) -> TBoolExc:
        manager = Workspace.get_data_manager()
        return manager.create_subdir(
            workspace.workspace_base_dir(),
            parents=[workspace.get_owner().user_base_dir()]
        )

    @classmethod
    def create(cls, name: str, owner: str | User, save: bool = True, open_on_create: bool = True) -> Workspace:

        result, msg = validate_workspace_experiment(name)
        if not result:
            raise ValueError(msg)

        owner = User.canonicalize(owner)
        now = datetime.utcnow()
        # noinspection PyArgumentList
        workspace = cls(
            name=name,
            status=Workspace.OPEN if open_on_create else Workspace.CLOSED,
            owner=owner,
            metadata=WorkspaceMetadata(created=now, last_modified=now),
        )
        if save:
            workspace.save(create=True)
            print(f"Created workspace '{workspace}' with id '{workspace.id}'.")
        return workspace

    # 5. Delete + callbacks
    @classmethod
    def before_delete(cls, workspace: Workspace) -> TBoolExc:
        try:
            if workspace.is_open():
                workspace.close()
            workspace.wait_experiments()
            # TODO Eliminare DataRepositories ed Experiments!
            return True, None
        except Exception as ex:
            return False, ex

    @classmethod
    def after_delete(cls, workspace: Workspace) -> TBoolExc:
        try:
            manager = Workspace.get_data_manager()
            return manager.remove_subdir(
                workspace.workspace_base_dir(),
                parents=[workspace.get_owner().user_base_dir()]
            )
        except Exception as ex:
            return False, ex

    @classmethod
    def delete(cls, workspace: Workspace):
        if workspace.is_open():
            return False, RuntimeError(f"Workspace '{workspace.get_name()}' is still open!")
        else:
            db.Document.delete(workspace)
            return True, None

    # 6. Read/Update Instance methods
    def __repr__(self):
        return f"Workspace <{self.name}> [uri = {self.uri}]"

    def get_id(self):
        return self.id

    def get_name(self) -> str:
        return self.name

    def get_owner(self) -> User:
        return self.owner

    def workspace_base_dir(self):
        return f"Workspace_{self.get_id()}"

    def rename(self, old_name: str, new_name: str) -> TBoolStr:
        if not self.is_open():
            return False, f"Workspace '{self.name}' is closed!"
        elif self.name != old_name:
            return False, "Old names are not equals!"
        else:
            self.name = new_name
            try:
                self.save()
                self.update_last_modified()
                return True, None
            except Exception as ex:
                return False, ex.args[0]

    def save(self, create=False):
        db.Document.save(self, force_insert=create)

    def update_last_modified(self, time: datetime = None, save: bool = True):
        self.metadata.update_last_modified(time)
        if save:
            self.save()

    def to_dict(self) -> TDesc:
        return {
            'name': self.name,
            'status': self.status,
            'owner': self.owner.to_dict(),
            'metadata': self.metadata.to_dict(),
        }

    # 7. Query-like methods
    def data_repositories(self):
        return list(BaseDataRepository.get(self))

    def all_experiments(self):
        return NotImplemented

    def running_experiments(self):
        return NotImplemented

    # 8. Status methods
    def open(self, save: bool = True):
        self.status = Workspace.OPEN
        self.update_last_modified(save=save)

    def close(self, save: bool = True):
        self.status = Workspace.CLOSED
        self.update_last_modified(save=save)

    def is_open(self):
        return self.status == Workspace.OPEN

    # 9. Special methods
    def wait_experiments(self):
        return NotImplemented