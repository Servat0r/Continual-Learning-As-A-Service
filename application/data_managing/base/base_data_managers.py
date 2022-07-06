"""
Data managers for handling interaction between the used FS and Users / Workspaces.
"""
from __future__ import annotations
import os

from application.utils import TBoolExc, t, abstractmethod, Module


TFContent = t.TypeVar(
    'TFContent',
    bound=tuple[str, list[str], t.Optional[t.Any]],  # Any is file content or FileStorage (filename, dir, content)
)

TFRead = t.TypeVar(
    'TFRead',
    bound=tuple[str, list[str], t.Optional[int]],
)


class FilesContentReader(t.Iterable[TFContent]):

    def __init__(self, manager: BaseDataManager, files: t.Iterable[TFRead],
                 base_dir: list[str] = None, binary=True):
        self.manager = manager
        self.files = iter(files)
        self.base_dir = base_dir
        self.binary = binary

    def __next__(self) -> TFContent | None:
        fread = next(self.files, None)
        if fread is not None:
            return self.manager.read_from_file(fread, base_dir=self.base_dir, binary=self.binary)
        else:
            return None

    def __iter__(self) -> t.Iterator[TFContent]:
        return self


class BaseDataManager:
    """
    Data manager, holding a set of callbacks to call before/after user/workspace creation/deletion to interact
    with the underlying FS.
    """

    _DFL_ROOT_DIR = os.environ.get('BASEDIR', 'files')

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

    @staticmethod
    @abstractmethod
    def is_subpath(src_name: str, dest_name: str,
                   src_parents: list[str] = None, dest_parents: list[str] = None, strict=True) -> bool:
        pass

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
    def default_image_loader(self, impath: str):
        pass

    @abstractmethod
    def greyscale_image_loader(self, impath: str):
        pass

    @abstractmethod
    def create_subdir(self, dir_name: str, parents: list[str] = None) -> TBoolExc:
        pass

    @abstractmethod
    def remove_subdir(self, dir_name: str, parents: list[str] = None) -> TBoolExc:
        pass

    @abstractmethod
    def move_subdir(self, src_name: str, dest_name: str,
                    src_parents: list[str] = None, dest_parents: list[str] = None) -> TBoolExc:
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

    def create_files(self, files: list[TFContent], base_dir: list[str] = None) -> list[str]:
        created = []
        for item in iter(files):
            item2 = (
                item[0],
                base_dir + item[1] if base_dir is not None else item[1],
                item[2],
            )
            result, exc = self.create_file(item2)
            if result:
                path = '/'.join(item[1] + [item[0]])
                created.append(path)
            else:
                print(exc)
        return created

    @abstractmethod
    def read_from_file(self, data: TFRead, base_dir: list[str] = None, binary=True) -> t.Any | None:
        pass

    def get_file_pointer(self, file_name: str, dir_names: list[str], binary=True) -> t.TextIO | t.BinaryIO | None:
        pass

    def read_from_files(self, files: t.Iterable[TFRead],
                        base_dir: list[str] = None, binary=True) -> t.Iterable[TFContent]:
        return FilesContentReader(self, files, base_dir, binary)

    @abstractmethod
    def print_to_file(self, file_name: str, dir_names: list[str], *values: t.Any,
                      sep=' ', newline=True, append=True, flush=True) -> TBoolExc:
        pass

    @abstractmethod
    def write_to_file(self, data: TFContent, append=True, binary=True) -> TBoolExc:
        pass

    @abstractmethod
    def delete_file(self, file_name: str, dir_names: list[str], binary=True,
                    return_content=False) -> t.AnyStr | None:
        pass

    @abstractmethod
    def save_model(self, model: Module, dir_names: list[str], model_name='model.pt') -> TBoolExc:
        pass

    @abstractmethod
    def add_archive(self, stream, base_path_list: list[str], tmp_archive_name='tmp_file',
                    archive_type='zip') -> tuple[int, list[str]]:
        pass

    @abstractmethod
    def rename_file(self, old_name: str, parents: list[str], new_name: str):
        pass


__all__ = [
    'TFRead',
    'TFContent',
    'BaseDataManager',
    'FilesContentReader',
]