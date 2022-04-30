from __future__ import annotations

from application.resources import *
from application.validation import *
from application.database import db
from application.models import User, Workspace, default_create_func
from application.mongo.mongo_base_metadata import MongoBaseMetadata


class WorkspaceMetadata(MongoBaseMetadata):

    def to_dict(self) -> TDesc:
        result = super().to_dict()
        return result

    @classmethod
    def from_dict(cls, data: TDesc) -> t.Any:
        raise NotImplementedError


@Workspace.set_class
class MongoWorkspace(Workspace, db.Document):

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

    @property
    def uri(self):
        context = UserWorkspaceResourceContext(self.owner.get_name(), self.name)
        return self.dfl_uri_builder(context)

    @classmethod
    @abstractmethod
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

    def __repr__(self):
        return f"Workspace <{self.name}> [uri = {self.uri}]"

    @abstractmethod
    def get_name(self) -> str:
        return self.name

    @abstractmethod
    def get_owner(self) -> User:
        return self.owner

    @classmethod
    @abstractmethod
    def get_by_owner(cls, owner: str | User):
        owner = User.canonicalize(owner)
        return cls.objects(owner=owner).all()

    @classmethod
    @abstractmethod
    def create(cls, name: str, owner: str | User, create_func: t.Callable = default_create_func,
               save: bool = True, open_on_create: bool = True):

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
        result, msg = create_func(workspace)
        if not result:
            raise ValueError(msg)
        elif save:
            workspace.save(force_insert=True)
        return workspace

    @abstractmethod
    def delete(self):
        if self.is_open():
            raise RuntimeError(f"Workspace '{self.name}' is still open!")
        else:
            db.Document.delete(self)

    @abstractmethod
    def open(self, save: bool = True):
        self.status = Workspace.OPEN
        self.metadata.update_last_modified()
        if save:
            self.save()

    @abstractmethod
    def close(self, save: bool = True):
        self.status = Workspace.CLOSED
        self.metadata.update_last_modified()
        if save:
            self.save()

    @abstractmethod
    def update_last_modified(self, save: bool = True):
        self.metadata.update_last_modified()
        if save:
            self.save()

    @abstractmethod
    def is_open(self):
        return self.status == Workspace.OPEN

    @classmethod
    def from_dict(cls, data: TDesc) -> t.Any:
        raise NotImplementedError

    @abstractmethod
    def to_dict(self) -> TDesc:
        return {
            'name': self.name,
            'status': self.status,
            'owner': self.owner.to_dict(),
            'metadata': self.metadata.to_dict(),
        }