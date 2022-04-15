from __future__ import annotations
import os
from datetime import datetime
from application.mongo_resources.mongo_base_metadata import BaseMetadata
from application.models.users import User
from mongoengine import NotUniqueError
from resources import *
from application.mongo_resources.commons_test import *
from application.validation import *
from application.database import db
from application.utils import *


def _default_create_func(workspace: Workspace) -> tuple[bool, str | None]:
    wdir = os.path.join(os.getcwd(), 'files', 'workspaces', workspace.owner.username, workspace.name)
    print(f"wdir = {wdir}")
    try:
        os.makedirs(wdir, exist_ok=True)
    except FileExistsError:
        return False, 'Workspace already existing!'
    with open(os.path.join(wdir, 'meta.json'), 'w') as f:
        f.write(r'{}')
    return True, None


class WorkspaceMetadata(BaseMetadata):

    def to_dict(self) -> TDesc:
        result = super().to_dict()
        return result

    @classmethod
    def from_dict(cls, data: TDesc) -> t.Any:
        raise NotImplementedError


class Workspace(JSONSerializable, URIBasedResource, db.Document):

    OPEN = 'OPEN'
    CLOSED = 'CLOSED'

    name = db.StringField(max_length=WORKSPACE_EXPERIMENT_MAX_CHARS, unique=True)
    uri = db.StringField(unique=True)
    status = db.StringField(max_length=8)
    owner = db.ReferenceField(User)
    metadata = db.EmbeddedDocumentField(WorkspaceMetadata)

    @classmethod
    def get_by_uri(cls, uri: str):
        return Workspace.objects(uri=uri).first()

    @classmethod
    def dfl_uri_builder(cls, context: UserWorkspaceResourceContext) -> str:
        username = context.names_dict()[context.dfl_username()]
        workspace = context.names_dict()[context.dfl_wname()]
        return cls.uri_separator().join(['workspace', username, workspace])

    @classmethod
    def canonicalize(cls, obj: UserWorkspaceResourceContext | Workspace):
        if isinstance(obj, UserWorkspaceResourceContext):
            context = obj
            uri = Workspace.dfl_uri_builder(context)
            return Workspace.get_by_uri(uri)
        elif isinstance(obj, Workspace):
            return obj
        else:
            raise TypeError(f"Unknown type: '{type(obj)}'.")

    def __repr__(self):
        return f"Workspace <{self.name}> [uri = {self.uri}]"

    def __str__(self):
        return self.__repr__()

    @classmethod
    def get_by_owner(cls, owner: str | User):
        owner = User.canonicalize(owner)
        return Workspace.objects(owner=owner).all()

    @classmethod
    def create(cls, name: str, owner: str | User, create_func: t.Callable = _default_create_func,
               save: bool = True, open_on_create: bool = True):

        result, msg = validate_workspace_experiment(name)
        if not result:
            raise ValueError(msg)

        owner = User.canonicalize(owner)
        context = DictUserWorkspaceResourceContext(owner.username, name)
        uri = cls.dfl_uri_builder(context)
        now = datetime.utcnow()
        # noinspection PyArgumentList
        workspace = Workspace(
            name=name,
            uri=uri,
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

    def delete(self):
        if self.is_open():
            raise RuntimeError(f"Workspace '{self.name}' is still open!")
        else:
            db.Document.delete(self)

    def open(self, save: bool = True):
        self.status = Workspace.OPEN
        if save:
            self.save()

    def close(self, save: bool = True):
        self.status = Workspace.CLOSED
        if save:
            self.save()

    def update_last_modified(self, save: bool = True):
        self.metadata.update_last_modified()  
        if save:
            self.save()

    def is_open(self):
        return self.status == Workspace.OPEN

    @classmethod
    def from_dict(cls, data: TDesc) -> t.Any:
        raise NotImplementedError

    def to_dict(self) -> TDesc:
        return {
            'id': str(self.id),
            'name': self.name,
            'status': self.status,
            'uri': self.uri,
            'owner': self.owner.to_dict(),
            'metadata': self.metadata.to_dict(),
        }


__all__ = [
    'URI_SEPARATOR',
    'make_uri',
    'split_uri',
    'Workspace',
    'WorkspaceMetadata',
]