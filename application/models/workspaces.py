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

    # ....................... #
    @classmethod
    def canonicalize(cls, obj: UserWorkspaceResourceContext | Workspace | tuple[str | User, str | Workspace]):
        if isinstance(obj, Workspace):
            return obj
        elif isinstance(obj, UserWorkspaceResourceContext):
            owner = obj.get_username()
            wname = obj.get_workspace()
            ws = Workspace.get(owner, wname)
            if ws is None or len(ws) < 1:
                raise ValueError(f"Such workspace (name = {wname}, owner = {owner}) does not exist!")
            else:
                return ws[0]
        elif isinstance(obj, tuple):
            if len(obj) != 2:
                raise ValueError(f"Incorrect tuple length for workspace canonicalize!")
            if isinstance(obj[1], Workspace):
                return obj[1]
            owner = obj[0]
            wname = obj[1]
            ws = Workspace.get(owner, wname)
            if ws is None or len(ws) < 1:
                raise ValueError(f"Such workspace (name = {wname}, owner = {owner}) does not exist!")
            else:
                return ws[0]
        else:
            raise TypeError(f"Unknown type: '{type(obj)}'.")

    @classmethod
    @abstractmethod
    def get_by_uri(cls, uri: str):
        return Workspace.get_class().get_by_uri(uri)

    @classmethod
    @abstractmethod
    def get(cls, owner: str | User = None, name: str = None) -> list[Workspace]:
        return Workspace.get_class().get(owner, name)

    @classmethod
    @abstractmethod
    def get_by_owner(cls, owner: str | User):
        return Workspace.get_class().get_by_owner(owner)

    @classmethod
    @abstractmethod
    def all(cls):
        return Workspace.get_class().all()
    # ....................... #

    @property
    @abstractmethod
    def uri(self):
        pass

    @classmethod
    def dfl_uri_builder(cls, context: UserWorkspaceResourceContext) -> str:
        username = context.get_username()
        workspace = context.get_workspace()
        return cls.uri_separator().join(['workspace', username, workspace])
    # ....................... #

    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_owner(self) -> User:
        pass

    def __str__(self):
        return self.__repr__()

    @classmethod
    @abstractmethod
    def create(cls, name: str, owner: str | User, create_func: t.Callable = default_create_func,
               save: bool = True, open_on_create: bool = True) -> Workspace:
        return Workspace.get_class().create(name, owner, create_func, save, open_on_create)

    @abstractmethod
    def rename(self, old_name: str, new_name: str) -> TBoolStr:
        return Workspace.get_class().rename(self, old_name, new_name)

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