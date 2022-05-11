from __future__ import annotations

from application.utils import TBoolExc, t, abstractmethod
from application.resources.utils import *
from application.resources.contexts import *
from application.models import User, Workspace


class BaseDataRepository(JSONSerializable, URIBasedResource):

    # 0.0. Actual class methods
    __data_repo_class__: t.Type[BaseDataRepository] = None

    @staticmethod
    def set_class(cls):
        if BaseDataRepository.__data_repo_class__ is None:
            BaseDataRepository.__data_repo_class__ = cls
        return cls

    @staticmethod
    def get_class():
        return BaseDataRepository.__data_repo_class__

    # 2. Uri methods
    @classmethod
    @abstractmethod
    def get_by_uri(cls, uri: str):
        return BaseDataRepository.get_class().get_by_uri(uri)

    @classmethod
    def dfl_uri_builder(cls, context: UserWorkspaceResourceContext, name: str) -> str:
        username = context.get_username()
        workspace = context.get_workspace()
        return cls.uri_separator().join(['DataRepository', username, workspace, name])

    # 3. General classmethods
    @classmethod
    def canonicalize(cls, obj: BaseDataRepository | UserWorkspaceResourceContext | tuple[str | User, str | Workspace],
                     name: str) -> BaseDataRepository:
        if isinstance(obj, BaseDataRepository):
            return obj
        else:
            workspace = Workspace.canonicalize(obj)
            repos = BaseDataRepository.get(workspace, name)
            if len(repos) != 1:
                raise ValueError(f"Such data repository (name = {name}, workspace = {workspace.uri}) does not exist!")
            return repos[0]

    @classmethod
    @abstractmethod
    def get(cls, workspace: Workspace = None, name: str = None, **kwargs) -> list[BaseDataRepository]:
        return cls.get_class().get(workspace, name, **kwargs)

    @classmethod
    def get_one(cls, workspace: Workspace = None, name: str = None, **kwargs) -> BaseDataRepository | None:
        repos = cls.get(workspace, name, **kwargs)
        if repos is not None and len(repos) >= 1:
            return repos[0]
        else:
            return None

    # 4. Create + callbacks
    @classmethod
    @abstractmethod
    def create(cls, name: str, workspace: Workspace, root: str = None,
               desc: str = None, save: bool = True) -> BaseDataRepository | None:
        return cls.get_class().create(name, workspace, root, desc, save)

    # 5. Delete + callbacks
    @abstractmethod
    def delete(self) -> TBoolExc:
        pass

    # 6. Read/Update Instance methods
    @abstractmethod
    def get_id(self):
        pass

    @abstractmethod
    def get_root(self) -> str:
        """
        Root directory
        :return:
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_description(self) -> str:
        pass

    @abstractmethod
    def get_workspace(self) -> Workspace:
        pass

    @abstractmethod
    def get_owner(self) -> User:
        pass

    @abstractmethod
    def get_absolute_path(self) -> str:
        pass

    @abstractmethod
    def save(self, create=False):
        pass

    @abstractmethod
    def data_repo_base_dir(self) -> str:
        pass

    @abstractmethod
    def add_directory(self, dir_name: str, parents: list[str] = None) -> bool:
        pass

    @abstractmethod
    def add_file(self, file_name: str, file_content, parents: list[str] = None) -> bool:
        pass