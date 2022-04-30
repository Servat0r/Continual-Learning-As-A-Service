from __future__ import annotations
from datetime import datetime

from application.resources.base.base_datatypes import *


class BaseMetadata(JSONSerializable):

    def to_dict(self) -> TDesc:
        return {
            'created': self.get_created(),
            'last_modified': self.get_last_modified(),
        }

    @classmethod
    @abstractmethod
    def from_dict(cls, data: TDesc) -> t.Any:
        raise NotImplementedError

    @abstractmethod
    def get_created(self):
        pass

    @abstractmethod
    def get_last_modified(self):
        pass

    @abstractmethod
    def set_last_modified(self, time):
        pass

    def update_last_modified(self, time=None):
        if time is None:
            time = datetime.utcnow()
        self.set_last_modified(time)


class BuildConfig(NameBasedResource):

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

    @abstractmethod
    def delete(self, context: ResourceContext):
        pass


class ResourceConfig(URIBasedResource):

    @classmethod
    @abstractmethod
    def get_by_uri(cls, uri: str):
        pass

    @classmethod
    @abstractmethod
    def dfl_uri_builder(cls, *args, **kwargs) -> str:
        pass

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