"""
Data managers for handling interaction between the used FS and Users / Workspaces.
"""
from __future__ import annotations
import os

from application.resources.utils import *


class BaseDataManager:
    """
    Data manager, holding a set of callbacks to call before/after user/workspace creation/deletion to interact
    with the underlying FS.
    """

    _DFL_ROOT_DIR = os.environ.get('BASEDIR') or 'files'

    __manager_class__: t.Type[BaseDataManager] = None

    @staticmethod
    def set_class(cls):
        if BaseDataManager.__manager_class__ is None:
            BaseDataManager.__manager_class__ = cls
        return cls

    @staticmethod
    def get_class():
        return BaseDataManager.__manager_class__

    @classmethod
    @abstractmethod
    def create(cls, root_dir: str = _DFL_ROOT_DIR, *args, **kwargs) -> BaseDataManager:
        return BaseDataManager.get_class().create(root_dir, *args, **kwargs)

    @abstractmethod
    def create_subdir(self, dir_name: str, parents: list[str] = None) -> TBoolExc:
        pass

    @abstractmethod
    def remove_subdir(self, dir_name: str, parents: list[str] = None) -> TBoolExc:
        pass

    @abstractmethod
    def get_dir_path(self, dir_names: list[str] = None) -> str:
        pass

    @abstractmethod
    def get_file_path(self, file_name: str, dir_names: list[str] = None) -> str:
        pass

    # metodi per aggiungere/togliere files etc.
    @abstractmethod
    def create_file(self, file_name: str, dir_names: list[str], file_content = None) -> bool:
        pass