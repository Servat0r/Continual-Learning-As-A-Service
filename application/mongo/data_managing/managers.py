from __future__ import annotations
import shutil

from application import TFRead, TFContent
from application.utils import t, TBoolExc, os

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

    @staticmethod
    def is_subpath(src_name: str, dest_name: str,
                   src_parents: list[str] = None, dest_parents: list[str] = None, strict=True) -> bool:
        src = src_parents.copy()
        dest = dest_parents.copy()
        src.append(src_name)
        dest.append(dest_name)

        if len(src) > len(dest):
            return False
        else:
            subpath = all(src[i] == dest[i] for i in range(len(src)))
            if subpath:
                return True if strict else (len(src) < len(dest))
            else:
                return False

    @classmethod
    def create(cls, root_dir: str = BaseDataManager._DFL_ROOT_DIR, *args, **kwargs) -> MongoLocalDataManager:
        manager = cls(root_dir)
        return manager

    def get_root(self):
        return self.root_dir

    def create_subdir(self, dir_name: str, parents: list[str] = None) -> TBoolExc:
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

    def move_subdir(self, src_name: str, dest_name: str,
                    src_parents: list[str] = None, dest_parents: list[str] = None) -> TBoolExc:
        src_path = os.path.join(self.root_dir, *src_parents, src_name)
        dest_path = os.path.join(self.root_dir, *dest_parents, dest_name)
        try:
            shutil.move(src_path, dest_path)
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

    def create_file(self, data: TFContent) -> TBoolExc:
        pass

    def read_from_file(self, data: TFRead) -> t.Any | None:
        pass

    def create_files(self, files: dict[tuple[str, list[str]], t.Any | None]) -> int:
        pass

    def read_from_files(self, files: tuple[str, list[str], int | None]) -> dict[tuple[str, list[str]], t.Any]:
        pass

    def print_to_file(self, file_name: str, dir_names: list[str], *values: t.Any, sep=' ', newline=True, append=True):
        pass

    def write_to_file(self, file_name: str, dir_names: list[str], content, append=True):
        pass

    def delete_file(self, file_name: str, dir_names: list[str], return_content=False) -> t.AnyStr | None:
        pass


__all__ = ['MongoLocalDataManager']