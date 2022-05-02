from __future__ import annotations
import os

from .data_repositories import *


class BaseDataSubRepository(JSONSerializable, URIBasedResource):

    # 0.0. Actual class methods
    __data_sub_repo_class__: t.Type[BaseDataSubRepository] = None

    @staticmethod
    def set_class(cls):
        if BaseDataSubRepository.__data_sub_repo_class__ is None:
            BaseDataSubRepository.__data_sub_repo_class__ = cls
        return cls

    @staticmethod
    def get_class():
        return BaseDataSubRepository.__data_sub_repo_class__

    # 2. Uri methods
    @classmethod
    def get_by_uri(cls, uri: str):
        return cls.get_class().get_by_uri(uri)

    @classmethod
    def dfl_uri_builder(cls, subrepo: BaseDataSubRepository) -> str:
        repository = subrepo.get_data_repo()
        username = repository.get_owner().get_name()
        workspace = repository.get_workspace().get_name()
        name = subrepo.get_name()
        return cls.uri_separator().join(['DataSubRepository', username, workspace, repository.get_name(), name])

    # 3. General classmethods
    @classmethod
    @abstractmethod
    def get(cls, repository: BaseDataRepository = None, name: str = None):
        return cls.get_class().get(repository, name)

    @classmethod
    @abstractmethod
    def get_by_data_repository(cls, repository: BaseDataRepository) -> list[BaseDataSubRepository]:
        return cls.get_class().get_by_data_repository(repository)

    # 4. Create + callbacks
    @classmethod
    @abstractmethod
    def before_create(cls, name: str, repository: BaseDataRepository) -> TBoolExc:
        pass

    @classmethod
    @abstractmethod
    def after_create(cls, repository: BaseDataSubRepository) -> TBoolExc:
        pass

    @classmethod
    @abstractmethod
    def create(cls, name: str, repository: BaseDataRepository, root: str = None,
               save: bool = True) -> BaseDataSubRepository | None:

        result, exc = BaseDataSubRepository.get_class().before_create(name, repository)
        if not result:
            raise exc

        subrepo = BaseDataSubRepository.get_class().create(name, repository, root, save)

        if subrepo is not None:
            result, exc = BaseDataSubRepository.get_class().after_create(subrepo)
            if not result:
                BaseDataSubRepository.delete(subrepo)
                raise exc

        return subrepo

    # 5. Delete + callbacks
    @classmethod
    @abstractmethod
    def before_delete(cls, repository: BaseDataSubRepository) -> TBoolExc:
        pass

    @classmethod
    @abstractmethod
    def after_delete(cls, repository: BaseDataSubRepository) -> TBoolExc:
        pass

    @classmethod
    @abstractmethod
    def delete(cls, subrepo: BaseDataSubRepository) -> TBoolExc:

        result, exc = BaseDataSubRepository.get_class().before_delete(subrepo)
        if not result:
            return False, exc

        result, exc = BaseDataSubRepository.get_class().delete(subrepo)
        if not result:
            return False, exc
        else:
            result, exc = BaseDataSubRepository.get_class().after_delete(subrepo)
            if not result:
                return False, exc
            return True, None

    # 6. Read/Update Instance methods
    @abstractmethod
    def get_id(self):
        pass

    # TODO Modificare in list[str] da passare al manager!
    def get_absolute_path(self) -> str:
        self_path = self.get_root()
        repo_path = self.get_data_repo().get_absolute_path()
        return os.path.join(repo_path, self_path)

    @abstractmethod
    def get_root(self) -> str:
        pass

    @abstractmethod
    def get_data_repo(self) -> BaseDataRepository:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass

    def get_metadata(self, name: str):
        result = self.get_all_metadata()
        return result.get(name)

    @abstractmethod
    def get_all_metadata(self) -> TDesc:
        pass

    def get_metadatas(self, *names: str) -> TDesc:
        all_meta = self.get_all_metadata()
        result: TDesc = {}

        if names is None or len(names) == 0:
            result = all_meta
        else:
            for name in names:
                result[name] = all_meta.get(name)

        return result

    @abstractmethod
    def save(self, create=False):
        pass

    # 7. Query-like instance methods
    @abstractmethod
    def get_files(self):
        pass

    @abstractmethod
    def get_file(self, name: str):
        pass

    # 8. Status methods
    # TODO

    # 9. Special methods