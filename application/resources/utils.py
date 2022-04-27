from __future__ import annotations
import typing as t
from abc import *

TBoolStr = t.TypeVar('TBoolStr', bound=tuple[bool, t.Optional[str]])
TBoolAny = t.TypeVar('TBoolAny', bound=tuple[bool, t.Any])
TDesc = t.TypeVar('TDesc', bound=dict[str, t.Any])


def primitive_validate(tp: type) -> t.Callable[[t.Any], TBoolStr]:
    def validator(obj: t.Any):
        result = (type(obj) == tp)
        msg: str = None if result else f"Type of the given object is {type(obj).__name__}"
        return result, msg

    return validator


class JSONSerializable:

    @abstractmethod
    def to_dict(self) -> TDesc:
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: TDesc) -> t.Any:
        pass


class NameBasedResource:

    @classmethod
    @abstractmethod
    def get_by_name(cls, name: str) -> t.Optional[NameBasedResource]:
        pass


class URIBasedResource:

    @classmethod
    @abstractmethod
    def get_by_uri(cls, uri: str):
        pass

    @staticmethod
    def uri_separator() -> str:
        return '::'

    @classmethod
    @abstractmethod
    def dfl_uri_builder(cls, *args, **kwargs) -> str:
        pass


nbr_type = t.Type[NameBasedResource]
ubr_type = t.Type[URIBasedResource]