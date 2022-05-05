from __future__ import annotations
import os
import shutil

from application.resources import TBoolExc
from application.data_managing import BaseDataManager


@BaseDataManager.set_class
class MongoLocalDataManager(BaseDataManager):
    """
    A data manager that uses local filesystem together with MongoDB.
    Uses Mongo ObjectIDs to create directory names.
    """

    def __init__(self, root_dir: str):
        root_dir = os.path.abspath(root_dir)
        os.makedirs(root_dir, exist_ok=True)
        self.root_dir = root_dir

    @classmethod
    def create(cls, root_dir: str = BaseDataManager._DFL_ROOT_DIR, *args, **kwargs) -> MongoLocalDataManager:
        manager = cls(root_dir)
        return manager

    def create_subdir(self, dir_name: str, parents: list[str] = None):
        if parents is None:
            parents = []
        parents = tuple(parents)
        parent_path = os.path.join(self.root_dir, *parents)
        complete_path = os.path.join(parent_path, dir_name)
        try:
            os.makedirs(complete_path, exist_ok=True)
            return True, None
        except Exception as ex:
            return False, ex

    def remove_subdir(self, dir_name: str, parents: list[str] = None) -> TBoolExc:
        if parents is None:
            parents = []
        parents = tuple(parents)
        parent_path = os.path.join(self.root_dir, *parents)
        complete_path = os.path.join(parent_path, dir_name)
        try:
            shutil.rmtree(complete_path, ignore_errors=True)
            return True, None
        except Exception as ex:
            return False, ex

    def get_dir_path(self, dir_names: list[str] = None) -> str:
        if dir_names is None:
            dir_names = []
        dir_names = tuple(dir_names)
        return os.path.join(self.root_dir, *dir_names)

    def get_file_path(self, file_name: str, dir_names: list[str] = None) -> str:
        dir_path = self.get_dir_path(dir_names)
        return os.path.join(dir_path, file_name)