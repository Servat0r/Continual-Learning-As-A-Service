"""
Data managers for handling interaction between the used FS and Users / Workspaces.
"""
from __future__ import annotations

import os
from typing import Iterator

from application.resources.utils import *


TFContent = t.TypeVar(
    'TFContent',
    bound=tuple[str, list[str], t.Optional[t.Any]], # Any is file content or FileStorage
)

TFRead = t.TypeVar(
    'TFRead',
    bound=tuple[str, list[str], t.Optional[int]],
)


class BaseDataManager:
    """
    Data manager, holding a set of callbacks to call before/after user/workspace creation/deletion to interact
    with the underlying FS.
    """

    _DFL_ROOT_DIR = os.environ.get('BASEDIR') or 'files'

    __manager_class__: t.Type[BaseDataManager] = None
    __manager__: t.Type[__manager_class__] = None
    __manager_set__ = False

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
    def create(cls, root_address: str = _DFL_ROOT_DIR, *args, **kwargs) -> BaseDataManager:
        manager = cls.__manager__
        if not cls.__manager_set__:
            manager = cls.get_class().create(root_address, *args, **kwargs)
            cls.__manager__ = manager
            cls.__manager_set__ = True
        return manager

    @abstractmethod
    def get_root(self):
        pass

    @classmethod
    def get(cls) -> BaseDataManager:
        if not cls.__manager_set__:
            raise RuntimeError("There is no data manager set!")
        return cls.get_class().__manager__

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
    def create_file(self, data: TFContent) -> TBoolExc:
        pass

    def create_files(self, files: t.Iterable[TFContent]) -> int:
        created = 0
        for item in iter(files):
            result, exc = self.create_file(item)
            if result:
                created += 1
            else:
                print(exc)
        return created

    @abstractmethod
    def read_from_file(self, data: TFRead) -> t.Any | None:
        pass

    @abstractmethod
    def read_from_files(self, files: t.Iterable[TFRead]) -> t.Iterable[TFContent]:
        result = {}

        return result

    @abstractmethod
    def print_to_file(self, file_name: str, dir_names: list[str], *values: t.Any, sep=' ', newline=True, append=True):
        pass

    @abstractmethod
    def write_to_file(self, file_name: str, dir_names: list[str], content, append=True):
        pass

    @abstractmethod
    def delete_file(self, file_name: str, dir_names: list[str], return_content=False) -> t.AnyStr | None:
        pass


class FileContentIterator(t.Iterable[TFContent]):

    def __init__(self, files: t.Iterable[TFRead]):
        self.files = iter(files)

    def __iter__(self) -> t.Iterator[TFContent]:
        return self

    def __next__(self):
        item: TFRead = next(self.files)
        result = BaseDataManager.get().read_from_file(item)
        return item[0], item[1], result