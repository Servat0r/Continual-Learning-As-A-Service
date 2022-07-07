from __future__ import annotations
from datetime import datetime

from application.utils import abstractmethod, t, TBoolStr, TDesc
from application.resources.utils import *
from application.resources.contexts import *
from .base_datatypes import *


class BaseMetadata(JSONSerializable):

    def to_dict(self, links=True) -> TDesc:
        return {
            'created': self.get_created(),
            'last_modified': self.get_last_modified(),
        }

    @abstractmethod
    def get_created(self):
        pass

    @abstractmethod
    def get_last_modified(self):
        pass

    @abstractmethod
    def update_last_modified(self, time: datetime = None):
        pass


class EmbeddedBuildConfig(JSONSerializable):

    @classmethod
    @abstractmethod
    def validate_input(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        pass

    @classmethod
    @abstractmethod
    def create(cls, data: TDesc, context: ResourceContext, save: bool = True):
        pass


class BuildConfig(JSONSerializable, NameBasedResource):

    __CONFIGS__: TDesc = {}

    @staticmethod
    def register_build_config(name: str = None):
        def registerer(cls):
            nonlocal name
            if name is None:
                name = cls.__name__
            BuildConfig.__CONFIGS__[name] = cls
            return cls

        return registerer

    @staticmethod
    @abstractmethod
    def target_type() -> t.Type[DataType]:
        pass

    @classmethod
    def get_by_name(cls, name: str | TDesc):
        if isinstance(name, str):
            return cls.__CONFIGS__.get(name)
        elif isinstance(name, dict):
            cname = name.get('name')
            if cname is None:
                raise ValueError('Missing name')
            else:
                return cls.__CONFIGS__.get(cname)

    @classmethod
    def get_key(cls) -> str | None:
        for name, cl in cls.__CONFIGS__.items():
            if cls == cl:
                return name
        return None

    @classmethod
    @abstractmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        pass

    @classmethod
    @abstractmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: ResourceContext, save: bool = True):
        pass

    @abstractmethod
    def build(self, context: ResourceContext):
        pass

    @abstractmethod
    def update(self, data, context: ResourceContext):
        pass


class ResourceConfig(JSONSerializable, URIBasedResource):

    # .................... #
    @classmethod
    @abstractmethod
    def get(cls, owner=None, workspace=None, name: str = None) -> list[ResourceConfig]:
        pass

    @classmethod
    @abstractmethod
    def get_one(cls, owner=None, workspace=None, name: str = None, check_unique=False):
        pass

    @classmethod
    @abstractmethod
    def get_by_claas_urn(cls, urn: str):
        pass

    @classmethod
    @abstractmethod
    def all(cls):
        pass
    # .................... #

    @property
    @abstractmethod
    def claas_urn(self):
        pass

    @classmethod
    @abstractmethod
    def dfl_claas_urn_builder(cls, *args, **kwargs) -> str:
        pass
    # .................... #

    @staticmethod
    @abstractmethod
    def target_type() -> t.Type[DataType]:
        pass

    @staticmethod
    @abstractmethod
    def meta_type() -> t.Type[BaseMetadata]:
        pass

    @classmethod
    @abstractmethod
    def create(cls, data, context: ResourceContext, save: bool = True, **metadata):
        pass

    @classmethod
    @abstractmethod
    def validate_input(cls, data, context: ResourceContext) -> TBoolStr:
        pass

    @abstractmethod
    def build(self, context: ResourceContext):
        pass

    @abstractmethod
    def update(self, data, context):
        pass

    @abstractmethod
    def delete(self, context):
        pass


__all__ = [
    'BaseMetadata',
    'EmbeddedBuildConfig',
    'BuildConfig',
    'ResourceConfig',
]