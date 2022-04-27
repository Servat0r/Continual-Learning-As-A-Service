from __future__ import annotations
import os
from application.utils import *
from application.models.users import User
from application.resources import *


def default_create_func(workspace: Workspace) -> tuple[bool, str | None]:
    wdir = os.path.join(os.getcwd(), 'files', 'workspaces', workspace.get_owner().get_name(), workspace.get_name())
    print(f"wdir = {wdir}")
    try:
        os.makedirs(wdir, exist_ok=True)
    except FileExistsError:
        return False, 'Workspace already existing!'
    with open(os.path.join(wdir, 'meta.json'), 'w') as f:
        f.write(r'{}')
    return True, None


class Workspace(JSONSerializable, URIBasedResource):

    OPEN = 'OPEN'
    CLOSED = 'CLOSED'

    __workspace_class__: t.Type[Workspace] = None

    @staticmethod
    def set_class(cls):
        if Workspace.__workspace_class__ is None:
            Workspace.__workspace_class__ = cls
        return cls

    @staticmethod
    def get_class():
        return Workspace.__workspace_class__

    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_owner(self) -> User:
        pass

    @classmethod
    @abstractmethod
    def get_by_uri(cls, uri: str):
        return Workspace.get_class().get_by_uri(uri)

    @classmethod
    def dfl_uri_builder(cls, context: UserWorkspaceResourceContext) -> str:
        username = context.get_username()
        workspace = context.get_workspace()
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

    def __str__(self):
        return self.__repr__()

    @classmethod
    @abstractmethod
    def get_by_owner(cls, owner: str | User):
        return Workspace.get_class().get_by_owner(owner)

    @classmethod
    @abstractmethod
    def create(cls, name: str, owner: str | User, create_func: t.Callable = default_create_func,
               save: bool = True, open_on_create: bool = True) -> Workspace:
        return Workspace.get_class().create(name, owner, create_func, save, open_on_create)

    @abstractmethod
    def delete(self):
        pass

    @abstractmethod
    def open(self, save: bool = True):
        pass

    @abstractmethod
    def close(self, save: bool = True):
        pass

    @abstractmethod
    def update_last_modified(self, save: bool = True):
        pass

    @abstractmethod
    def is_open(self):
        pass

    @classmethod
    def from_dict(cls, data: TDesc) -> t.Any:
        raise NotImplementedError

    @abstractmethod
    def to_dict(self) -> TDesc:
        pass


__all__ = [
    'URI_SEPARATOR',
    'make_uri',
    'split_uri',
    'Workspace',
    'default_create_func',
]