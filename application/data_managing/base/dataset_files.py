from __future__ import annotations
import os

from application.resources import *


class BaseDatasetFile(JSONSerializable):

    # 0.0 Actual class methods
    __dataset_file_class__: t.Type[BaseDatasetFile] = None

    @staticmethod
    def set_class(cls):
        if BaseDatasetFile.__dataset_file_class__ is None:
            BaseDatasetFile.__dataset_file_class__ = cls
        return cls

    @staticmethod
    def get_class():
        return BaseDatasetFile.__dataset_file_class__

    # 4. Create + callbacks
    @classmethod
    @abstractmethod
    def before_create(cls, name: str, subrepo: str, relative_path: str,
                      content: t.Any = None, is_binary: bool = True) -> TBoolExc:
        pass

    @classmethod
    @abstractmethod
    def after_create(cls, dfile: BaseDatasetFile) -> TBoolExc:
        pass

    @classmethod
    @abstractmethod
    def create(cls, name: str, subrepo: str, relative_path: str, context: ResourceContext,
               content: t.Any = None, is_binary: bool = True, save: bool = True):
        pass

    # 5. Delete + callbacks
    @classmethod
    @abstractmethod
    def before_delete(cls, dfile: BaseDatasetFile) -> TBoolExc:
        pass

    @classmethod
    @abstractmethod
    def after_delete(cls, dfile: BaseDatasetFile) -> TBoolExc:
        pass

    @classmethod
    @abstractmethod
    def delete(cls, dfile: BaseDatasetFile):
        pass

    # 6. Read/Update Instance methods
    def get_absolute_path(self) -> str:
        self_path = self.get_relative_path()
        dataset_path = self.get_data_subrepo().get_absolute_path()
        return os.path.join(dataset_path, self_path)

    @abstractmethod
    def read(self):
        pass

    @abstractmethod
    def write(self, append=True):
        pass

    @abstractmethod
    def open(self):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def is_empty(self) -> bool:
        pass

    @abstractmethod
    def get_relative_path(self) -> str:
        """
        Current file path relative to the root of the data subrepo.
        :return:
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Current name.
        :return:
        """
        pass

    @abstractmethod
    def get_content_type(self) -> str:
        """
        Mimetype of file content (if applicable).
        :return:
        """
        pass

    @abstractmethod
    def get_label(self) -> int:
        """
        Label of the file (for classification tasks).
        :return:
        """
        pass

    @abstractmethod
    def update(self, data: TDesc, save: bool = True):
        """
        Syntax:
            "name" -> name
            "label" -> label
            "path" -> relative_path
            "content_type" -> content_type
        :param data:
        :param save:
        :return:
        """
        pass

    @abstractmethod
    def update_relative_path(self) -> str:
        pass

    @abstractmethod
    def update_name(self):
        pass

    @abstractmethod
    def update_content_type(self):
        pass

    @abstractmethod
    def update_label(self):
        pass

    # 9. Special methods
    @abstractmethod
    def reload(self):
        pass

    # -> data subrepo (reference) [dataset_root is the root of the corresponding data repo]
    # -> path (relative to data subrepo root)
    # -> name (a custom name)
    # -> content_type (mimetype)
    # -> label (classification!)
    # -> task_label (nullable)  [NO! Sono funzionali al Benchmark!]