from __future__ import annotations
import os
from application.utils import *
from application.models.users import User
from application.resources import *


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
    __data_manager__ = None

    @staticmethod
    def set_data_manager(manager) -> bool:
        if Workspace.__data_manager__ is None:
            Workspace.__data_manager__ = manager
            return True
        else:
            return False

    @staticmethod
    def get_data_manager():
        return Workspace.__data_manager__

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
    def get_id(self):
        pass

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
    def create(cls, name: str, owner: str | User, save: bool = True, open_on_create: bool = True,
               before_args: TDesc = None, after_args: TDesc = None) -> Workspace:
        
        if before_args is None:
            before_args = {}

        if after_args is None:
            after_args = {}

        result, exc = cls.get_data_manager().before_create_workspace(**before_args)
        if not result:
            raise exc

        workspace = Workspace.get_class().create(name, owner, save, open_on_create)

        if workspace is not None:
            result, exc = cls.get_data_manager().after_create_workspace(workspace, **after_args)
            if not result:
                Workspace.delete(workspace)
                raise exc

        return workspace

    @abstractmethod
    def rename(self, old_name: str, new_name: str) -> TBoolStr:
        return Workspace.get_class().rename(self, old_name, new_name)

    @abstractmethod
    def save(self, create=False):
        pass

    @classmethod
    @abstractmethod
    def delete(cls, workspace: Workspace, before_args: TDesc = None, after_args: TDesc = None) -> TBoolExc:

        if before_args is None:
            before_args = {}

        if after_args is None:
            after_args = {}

        result, exc = cls.get_data_manager().before_delete_workspace(workspace, **before_args)
        if not result:
            raise exc

        result, exc = Workspace.get_class().delete(workspace)
        if not result:
            raise exc
        else:
            result, exc = cls.get_data_manager().after_delete_workspace(workspace, **after_args)
            if not result:
                raise exc
            return True, None

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
]