from __future__ import annotations

from application.models import User, Workspace
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
    def get(cls, workspace: Workspace = None, name: str = None) -> list[BaseDataRepository]:
        pass

    # 4. Create + callbacks
    @classmethod
    @abstractmethod
    def before_create(cls, name: str, workspace: Workspace) -> TBoolExc:
        pass

    @classmethod
    @abstractmethod
    def after_create(cls, repository: BaseDataRepository) -> TBoolExc:
        pass

    @classmethod
    @abstractmethod
    def create(cls, name: str, workspace: Workspace, root: str = None, save: bool = True) -> BaseDataRepository | None:

        result, exc = BaseDataRepository.get_class().before_create(name, workspace)
        if not result:
            raise exc

        repository = BaseDataRepository.get_class().create(name, workspace, root, save)

        if repository is not None:
            result, exc = BaseDataRepository.get_class().after_create(repository)
            if not result:
                BaseDataRepository.delete(repository)
                raise exc

        return repository

    # 5. Delete + callbacks
    @classmethod
    @abstractmethod
    def before_delete(cls, repository: BaseDataRepository) -> TBoolExc:
        pass

    @classmethod
    @abstractmethod
    def after_delete(cls, repository: BaseDataRepository) -> TBoolExc:
        pass

    @classmethod
    @abstractmethod
    def delete(cls, repository: BaseDataRepository) -> TBoolExc:

        result, exc = BaseDataRepository.get_class().before_delete(repository)
        if not result:
            return False, exc

        result, exc = BaseDataRepository.get_class().delete(repository)
        if not result:
            return False, exc
        else:
            result, exc = BaseDataRepository.get_class().after_delete(repository)
            if not result:
                return False, exc
            return True, None

    # 6. Read/Update Instance methods
    @abstractmethod
    def get_id(self):
        pass

    @abstractmethod
    def get_root(self):
        """
        Root directory
        :return:
        """
        pass

    @abstractmethod
    def get_name(self):
        pass

    @abstractmethod
    def get_workspace(self):
        pass

    @abstractmethod
    def get_owner(self):
        pass

    @abstractmethod
    def get_absolute_path(self):
        pass

    @abstractmethod
    def save(self, create=False):
        pass

    @abstractmethod
    def data_repo_base_dir(self) -> str:
        pass

    # 7. Query-like instance methods
    @abstractmethod
    def get_sub_repositories(self):
        pass

    # 8. Status methods
    # TODO

    # 9. Special methods