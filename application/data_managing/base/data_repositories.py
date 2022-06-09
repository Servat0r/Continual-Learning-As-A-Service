from __future__ import annotations

from application.utils import TBoolExc, t, abstractmethod, normalize_map_field_path, denormalize_map_field_path
from application.models import User, Workspace
from .base_data_managers import TFContent

from application.resources.utils import *
from application.resources.contexts import *


TFContentLabel = t.TypeVar(
    'TFContentLabel',
    bound=tuple[TFContent, int]  # (file, label)
)


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
    @abstractmethod
    def get_by_claas_urn(cls, urn: str):
        return BaseDataRepository.get_class().get_by_claas_urn(urn)

    @classmethod
    def dfl_claas_urn_builder(cls, context: UserWorkspaceResourceContext, name: str) -> str:
        username = context.get_username()
        workspace = context.get_workspace()
        return cls.claas_urn_separator().join(['DataRepository', username, workspace, name])

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
    def add_file(self, file_name: str, file_content, label: int, parents: list[str] = None) -> TBoolExc:
        pass

    @abstractmethod
    def add_files(self, files: t.Iterable[TFContentLabel], locked=False, parents_locked=False) -> list[str]:
        pass

    @abstractmethod
    def add_archive(self, stream, labels: dict, base_path_list: list[str], archive_type='zip', locked=False,
                    parents_locked=False) -> tuple[int, list[str]]:     # total_files_retrieved, added_files
        pass

    @abstractmethod
    def move_directory(self, src_name: str, dest_name: str,
                       src_parents: list[str] = None, dest_parents: list[str] = None) -> TBoolExc:
        pass

    @abstractmethod
    def delete_directory(self, dir_name: str, dir_parents: list[str] = None) -> TBoolExc:
        pass

    @abstractmethod
    def get_file_label(self, file_path: str) -> int:
        pass

    @abstractmethod
    def get_all_files(self, root_path: str, include_labels=True) -> tuple[list[str], list[int]]:
        pass


__all__ = [
    'TFContentLabel',
    'BaseDataRepository',
]