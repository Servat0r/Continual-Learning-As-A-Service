from __future__ import annotations
import os

from application.utils import *
from application.resources.utils import *


class BaseDataRepository:

    __data_repo_class__: t.Type[BaseDataRepository] = None

    @staticmethod
    def set_class(cls):
        if BaseDataRepository.__data_repo_class__ is None:
            BaseDataRepository.__data_repo_class__ = cls
        return cls

    @staticmethod
    def get_class():
        return BaseDataRepository.__data_repo_class__

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
    def get_sub_repositories(self):
        pass

    @abstractmethod
    def get_absolute_path(self):
        pass

