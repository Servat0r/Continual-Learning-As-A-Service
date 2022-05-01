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
        return BaseDataManager.__manager_class__.create(root_dir, *args, **kwargs)

    @abstractmethod
    def before_create_user(self, *args, **kwargs) -> TBoolExc:
        """
        To call before a user is created.
        :return:
        """
        pass

    @abstractmethod
    def after_create_user(self, user, *args, **kwargs) -> TBoolExc:
        pass

    @abstractmethod
    def before_delete_user(self, user, *args, **kwargs) -> TBoolExc:
        pass

    @abstractmethod
    def after_delete_user(self, user, *args, **kwargs) -> TBoolExc:
        pass

    @abstractmethod
    def before_create_workspace(self, *args, **kwargs) -> TBoolExc:
        pass

    @abstractmethod
    def after_create_workspace(self, workspace, *args, **kwargs) -> TBoolExc:
        pass

    @abstractmethod
    def before_delete_workspace(self, workspace, *args, **kwargs) -> TBoolExc:
        pass

    @abstractmethod
    def after_delete_workspace(self, workspace, *args, **kwargs) -> TBoolExc:
        pass

    # metodi per aggiungere/togliere files etc.