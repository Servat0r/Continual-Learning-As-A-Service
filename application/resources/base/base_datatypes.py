# Base datatypes.
from __future__ import annotations

from abc import ABC

from application.resources.base.base_contexts import *


class DataType:

    __datatypes: dict[str, t.Type[DataType]] = {}

    @classmethod
    def default_typename(cls) -> str:
        """
        Default typename (name of the class).
        :return:
        """
        return cls.__name__

    @classmethod
    def canonical_typename(cls) -> str:
        """
        "Super" typename (name of a common 'interface' for overwriting default one).
        :return:
        """
        return cls.__name__

    @staticmethod
    def canonicalize(resource_type: str | t.Type[ReferrableDataType]) -> TBoolStr:
        """
        Canonization for parameters passed as resource_type.
        :param resource_type:
        :return:
        """
        if isinstance(resource_type, str):
            return True, resource_type
        elif issubclass(resource_type, ReferrableDataType):
            return True, resource_type.canonical_typename()
        else:
            return False, None

    @classmethod
    def type_aliases(cls) -> set[str]:
        result = {cls.default_typename(), cls.canonical_typename()}
        for item in DataType.__datatypes.items():
            if item[1] == cls:
                result.add(item[0])
        return result

    @staticmethod
    def get_all_typenames() -> dict[str, t.Type[DataType]]:
        return DataType.__datatypes.copy()

    @staticmethod
    def set_resource_type(aliases: list[str] | None = None, canonical_typename: bool = True):
        def setter(cls: t.Type[DataType]):
            nonlocal aliases, canonical_typename
            if aliases is None:
                aliases = set()
            else:
                aliases = set(aliases)
            aliases.add(cls.default_typename())
            for name in aliases:
                DataType.__datatypes[name] = cls
            if canonical_typename:
                DataType.__datatypes[cls.canonical_typename()] = cls
            return cls
        return setter

    @staticmethod
    def get_type(name: str) -> t.Type[DataType] | None:
        return DataType.__datatypes.get(name)

    @classmethod
    @abstractmethod
    def validate_data(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        pass

    @classmethod
    def build_from_data(cls, name: str, context: ResourceContext) -> DataType:
        pass


class WrapperDataType(DataType, ABC):

    def __init__(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def set_value(self, new_value):
        self.value = new_value


class ReferrableDataType(DataType, URIBasedResource):

    """
    "Interface-mixin" for referrable resources that rely on external storage.
    """
    @staticmethod
    @abstractmethod
    def config_type():
        pass

    @abstractmethod
    def set_metadata(self, **kwargs):
        for item in kwargs.items():
            self.metadata[item[0]] = item[1]

    @abstractmethod
    def get_metadata(self, key: str | None = None) -> TDesc | t.Any:
        if key is None:
            return self.metadata.copy()
        else:
            return self.metadata[key]

    @classmethod
    def validate_data(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        """
        "Wrapper" validation method.
        :param data:
        :param context:
        :return:
        """
        cfg_type = cls.config_type()
        return cfg_type.validate_input(data, context)

    @classmethod
    def build_from_data(cls, name: str, context: ResourceContext) -> ReferrableDataType:
        cfg_type = cls.config_type()
        uri = cfg_type.dfl_uri_builder(context, name)
        resource_config = cfg_type.get_by_uri(uri)
        return resource_config.build(context) if resource_config is not None else None

    def __init__(self):
        self.metadata: TDesc = {}


class WrapperReferrableDataType(WrapperDataType, ReferrableDataType, ABC):

    def __init__(self, value):
        WrapperDataType.__init__(self, value)
        ReferrableDataType.__init__(self)
