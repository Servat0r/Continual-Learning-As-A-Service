from __future__ import annotations

import sys
import traceback

import torch
import shutil
import warnings
from zipfile import ZipFile
from PIL import Image

from application import TFRead, TFContent
from application.utils import t, TBoolExc, os, Module, auto_tboolexc

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

    @auto_tboolexc
    def create_subdir(self, dir_name: str, parents: list[str] = None) -> TBoolExc:
        if parents is None:
            parents = []
        parents = tuple(parents)
        parent_path = os.path.join(self.root_dir, *parents)
        complete_path = os.path.join(parent_path, dir_name)
        os.makedirs(complete_path, exist_ok=True)
        return True, None

    @auto_tboolexc
    def move_subdir(self, src_name: str, dest_name: str,
                    src_parents: list[str] = None, dest_parents: list[str] = None) -> TBoolExc:
        src_path = os.path.join(self.root_dir, *src_parents, src_name)
        dest_path = os.path.join(self.root_dir, *dest_parents, dest_name)
        shutil.move(src_path, dest_path)
        return True, None

    @auto_tboolexc
    def remove_subdir(self, dir_name: str, parents: list[str] = None) -> TBoolExc:
        if parents is None:
            parents = []
        parents = tuple(parents)
        parent_path = os.path.join(self.root_dir, *parents)
        complete_path = os.path.join(parent_path, dir_name)
        shutil.rmtree(complete_path, ignore_errors=True)
        return True, None

    def get_dir_list(self, dir_names: list[str] = None) -> list[str]:
        if dir_names is None:
            dir_names = []
        return [self.get_root()] + dir_names

    def get_dir_path(self, dir_names: list[str] = None) -> str:
        dir_list = self.get_dir_list(dir_names)
        return os.path.join(*dir_list)

    def get_file_path(self, file_name: str, dir_names: list[str] = None) -> str:
        dir_path = self.get_dir_path(dir_names)
        return os.path.join(dir_path, file_name)

    @auto_tboolexc
    def create_file(self, data: TFContent) -> TBoolExc:
        dir_list = self.get_dir_list(data[1])
        result, exc = self.create_subdir(dir_list[-1], dir_list[:-1])
        if not result:
            return result, exc

        fpath = os.path.join(self.get_root(), self.get_file_path(data[0], data[1]))
        fstorage = data[2]
        if fstorage is not None:
            fstorage.save(fpath)
        else:
            # noinspection PyUnusedLocal
            with open(fpath, 'w') as f:
                pass
        return True, None

    def read_from_file(self, data: TFRead, base_dir: list[str] = None, binary=True) -> t.Any | None:
        base_dir = [] if base_dir is None else base_dir
        fpath = os.path.join(self.get_root(), *base_dir, *data[1], data[0])
        mode = 'rb' if binary else 'r'
        if os.path.exists(fpath):
            with open(fpath, mode) as f:
                content = f.read(data[2])
            return content
        else:
            return None

    def get_file_pointer(self, file_name: str, dir_names: list[str], binary=True) -> t.TextIO | t.BinaryIO | None:
        fpath = os.path.join(self.get_root(), *dir_names, file_name)
        mode = 'rb' if binary else 'r'
        return open(fpath, mode)

    @auto_tboolexc
    def print_to_file(self, file_name: str, dir_names: list[str], *values: t.Any,
                      sep=' ', newline=True, append=True, flush=True) -> TBoolExc:
        fpath = os.path.join(self.get_root(), *dir_names, file_name)
        with open(fpath, 'a' if append else 'w') as f:
            end = None if newline else ''
            print(*values, sep=sep, file=f, end=end, flush=flush)
        return True, None

    @auto_tboolexc
    def write_to_file(self, data: TFContent, append=True, binary=True) -> TBoolExc:
        fpath = os.path.join(self.get_root(), *data[1], data[0])
        mode = ('a' if append else 'w') + ('b' if binary else '')
        with open(fpath, mode) as f:
            f.write(data[2])
        return True, None

    def delete_file(self, file_name: str, dir_names: list[str], binary=True,
                    return_content=False) -> t.AnyStr | None:
        fpath = os.path.join(self.get_root(), *dir_names, file_name)
        content = None
        if os.path.exists(fpath):
            if return_content:
                mode = 'rb' if binary else 'r'
                with open(fpath, mode) as f:
                    content = f.read()
            os.remove(fpath)
        else:
            warnings.warn(f"The file {fpath} does not exist.")
        return content

    @auto_tboolexc
    def save_model(self, model: Module, dir_names: list[str], model_name='model.pt') -> TBoolExc:
        fpath = os.path.join(self.get_root(), *dir_names, model_name)
        result, exc = self.create_file((model_name, [self.get_root()] + dir_names, None))
        if not result:
            exc.args[0] = f"Failed to create file '{model_name}': {exc.args[0]}."
            return result, exc
        torch.save(model, fpath)
        return True, None

    def add_archive(self, stream, base_path_list: list[str], tmp_archive_name='tmp_file',
                    archive_type='zip') -> tuple[int, list[str]]:
        total = 0
        created: list[str] = []
        archive_file_name = f"{tmp_archive_name}.{archive_type}"
        result, exc = self.create_file((archive_file_name, base_path_list, stream))
        if not result:
            print(exc)
            traceback.print_exception(*sys.exc_info())
        else:
            archive_path = self.get_file_path(archive_file_name, base_path_list)
            archive_dir_path = self.get_dir_path(base_path_list)
            with ZipFile(archive_path, 'r') as zipf:
                zipf.printdir()
                namelist = zipf.namelist()
                total = len(namelist)
                for file_name in namelist:
                    print(file_name)
                    file_name_2 = file_name
                    zipf.extract(file_name, path=archive_dir_path)
                    created.append(file_name_2)
            self.delete_file(archive_file_name, base_path_list)
        return total, created

    def default_image_loader(self, impath: str):
        return Image.open(impath).convert('RGB')

    def greyscale_image_loader(self, impath: str):
        return Image.open(impath).convert('L')

    @auto_tboolexc
    def rename_directory(self, old_name: str, parents: list[str], new_name: str):
        old_path = self.get_dir_path(parents + [old_name])
        new_path = self.get_dir_path(parents + [new_name])
        os.rename(old_path, new_path)

    @auto_tboolexc
    def rename_file(self, old_name: str, parents: list[str], new_name: str):
        old_path = self.get_file_path(old_name, parents)
        new_path = self.get_file_path(new_name, parents)
        os.rename(old_path, new_path)

    def __repr__(self):
        return f"{type(self).__name__} <root_dir = {self.root_dir}>"

    def __str__(self):
        return self.__repr__()


__all__ = ['MongoLocalDataManager']