from __future__ import annotations

from application.utils import TBoolExc, t, abstractmethod, TDesc, TBoolStr, \
    normalize_map_field_path, denormalize_map_field_path
from application.models import User, Workspace
from .base_data_managers import TFContent

from application.resources.utils import *
from application.resources.contexts import *


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

    @staticmethod
    def normalize(s: str):
        return normalize_map_field_path(s)

    @staticmethod
    def denormalize(s: str):
        return denormalize_map_field_path(s)

    # 2. Uri methods
    @classmethod
    def get_by_claas_urn(cls, urn: str):
        s = urn.split(cls.claas_urn_separator())
        username = s[2]
        wname = s[3]
        name = s[4]
        workspace = Workspace.canonicalize((username, wname))
        ls = cls.get(workspace=workspace, name=name)
        return ls[0] if len(ls) > 0 else None

    @classmethod
    def dfl_claas_urn_builder(cls, context: UserWorkspaceResourceContext, name: str) -> str:
        username = context.get_username()
        workspace = context.get_workspace()
        return cls.claas_urn_separator().join(['claas', 'DataRepository', username, workspace, name])

    @property
    def claas_urn(self):
        context = UserWorkspaceResourceContext(self.get_owner().get_name(), self.get_workspace().get_name())
        return self.dfl_claas_urn_builder(context, self.get_name())

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
                raise ValueError(f"Such data repository (name = {name}, workspace = {workspace.claas_urn}) does not exist!")
            return repos[0]

    @classmethod
    @abstractmethod
    def get(cls, workspace: Workspace = None, name: str = None, **kwargs) -> list[BaseDataRepository]:
        return cls.get_class().get(workspace, name, **kwargs)

    @classmethod
    def get_one(cls, workspace: Workspace = None, name: str = None, **kwargs) -> BaseDataRepository | None:
        if name is not None and workspace is not None:
            repos = cls.get(workspace, name, **kwargs)
            if repos is not None and len(repos) >= 1:
                return repos[0]
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
    def save(self, create=False) -> bool:
        pass

    @abstractmethod
    def data_repo_base_dir(self) -> str:
        pass

    @abstractmethod
    def add_directory(self, dir_name: str, parents: list[str] = None) -> TBoolExc:
        pass

    @abstractmethod
    def add_file(self, file_name: str, file_content, label: int, parents: list[str] = None, save=False) -> TBoolExc:
        pass

    @abstractmethod
    def add_files(self, files: t.Iterable[TFContent], locked=False, parents_locked=False) -> list[str]:
        pass

    @abstractmethod
    def add_archive(self, stream, base_path_list: list[str], archive_type='zip', locked=False,
                    parents_locked=False) -> tuple[int, list[str]]:     # total_files_retrieved, added_files
        pass

    @abstractmethod
    def move_directory(self, src_name: str, dest_name: str,
                       src_parents: list[str] = None, dest_parents: list[str] = None) -> TBoolExc:
        pass

    @abstractmethod
    def rename_directory(self, path: str, new_name: str) -> TBoolExc:
        pass

    @abstractmethod
    def delete_directory(self, dir_name: str, dir_parents: list[str] = None) -> TBoolExc:
        pass

    @abstractmethod
    def get_all_files(self, root_path: str) -> list[str]:
        pass

    @abstractmethod
    def delete_file(self, file_name: str, parents: list[str], locked=False, parents_locked=False, save=False) -> TBoolExc:
        pass

    @abstractmethod
    def delete_files(self, files: t.Iterable[tuple[str, list[str]]], locked=False, parents_locked=False) -> list[str]:
        pass

    @abstractmethod
    def update(self, updata: TDesc) -> TBoolStr:
        pass


__all__ = ['BaseDataRepository']