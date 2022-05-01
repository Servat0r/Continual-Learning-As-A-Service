from __future__ import annotations
import os

from application.utils import *
from application.resources.utils import *


class BaseDataSubRepository:

    __data_sub_repo_class__: t.Type[BaseDataSubRepository] = None

    @staticmethod
    def set_class(cls):
        if BaseDataSubRepository.__data_sub_repo_class__ is None:
            BaseDataSubRepository.__data_sub_repo_class__ = cls
        return cls

    @staticmethod
    def get_class():
        return BaseDataSubRepository.__data_sub_repo_class__

    def get_absolute_path(self) -> str:
        self_path = self.get_relative_path()
        repo_path = self.get_data_repo().get_absolute_path()
        return os.path.join(repo_path, self_path)

    @abstractmethod
    def get_relative_path(self) -> str:
        pass

    @abstractmethod
    def get_data_repo(self) -> BaseDataRepository:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_metadata(self, name: str):
        pass

    @abstractmethod
    def get_all_metadata(self) -> TDesc:
        pass

    @abstractmethod
    def get_metadatas(self, *names: str) -> TDesc:
        result: TDesc = {}
        if names is None or len(names) == 0:
            return self.get_all_metadata()
        else:
            for name in names:
                val = self.get_metadata(name)
                if val is not None:     # TODO Nullables?
                    result[name] = val
            return result