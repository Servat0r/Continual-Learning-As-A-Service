from __future__ import annotations
from datetime import datetime

from application.utils import TBoolStr, TBoolExc, TDesc, t, abstractmethod
from application.resources.utils import *
from application.resources.contexts import *
from .users import User


class Workspace(JSONSerializable, URIBasedResource):

    @staticmethod
    def data_base_dir() -> str:
        return f"Data"

    @staticmethod
    def experiments_base_dir() -> str:
        return f"Experiments"

    OPEN = 'OPEN'
    CLOSED = 'CLOSED'

    # 0.0. Actual class methods
    __workspace_class__: t.Type[Workspace] = None

    @staticmethod
    def set_class(cls):
        if Workspace.__workspace_class__ is None:
            Workspace.__workspace_class__ = cls
        return cls

    @staticmethod
    def get_class():
        return Workspace.__workspace_class__

    # 2. Uri methods
    @classmethod
    @abstractmethod
    def get_by_uri(cls, uri: str):
        return Workspace.get_class().get_by_uri(uri)

    @classmethod
    def dfl_uri_builder(cls, context: UserWorkspaceResourceContext) -> str:
        username = context.get_username()
        workspace = context.get_workspace()
        return cls.uri_separator().join(['workspace', username, workspace])

    # 3. General classmethods
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
    def get(cls, owner: str | User = None, name: str = None, **kwargs) -> list[Workspace]:
        return Workspace.get_class().get(owner, name, **kwargs)

    @classmethod
    @abstractmethod
    def get_by_owner(cls, owner: str | User):
        return Workspace.get_class().get_by_owner(owner)

    @classmethod
    @abstractmethod
    def all(cls):
        return Workspace.get_class().all()

    # 4. Create + callbacks
    @classmethod
    @abstractmethod
    def create(cls, name: str, owner: str | User, save: bool = True, open_on_create: bool = True) -> Workspace:
        return cls.get_class().create(name, owner, save, open_on_create)

    # 5. Delete + callbacks
    @abstractmethod
    def delete(self) -> TBoolExc:
        pass

    # 6. Read/Update Instance methods
    def __str__(self):
        return self.__repr__()

    @abstractmethod
    def get_id(self):
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_owner(self) -> User:
        pass

    @abstractmethod
    def workspace_base_dir(self) -> str:
        pass

    @abstractmethod
    def data_base_dir_parents(self) -> list[str]:
        pass

    @abstractmethod
    def experiments_base_dir_parents(self) -> list[str]:
        pass

    @abstractmethod
    def rename(self, old_name: str, new_name: str) -> TBoolStr:
        return Workspace.get_class().rename(self, old_name, new_name)

    @abstractmethod
    def save(self, create=False):
        pass

    @abstractmethod
    def update_last_modified(self, time: datetime = None, save: bool = True):
        pass

    @abstractmethod
    def to_dict(self) -> TDesc:
        pass

    # 7. Query-like methods
    @abstractmethod
    def data_repositories(self):
        pass

    @abstractmethod
    def all_experiments(self):
        pass

    @abstractmethod
    def running_experiments(self):
        pass

    # 8. Status methods
    @abstractmethod
    def open(self, save: bool = True):
        pass

    @abstractmethod
    def close(self, save: bool = True):
        pass

    @abstractmethod
    def is_open(self):
        pass


__all__ = ['Workspace']