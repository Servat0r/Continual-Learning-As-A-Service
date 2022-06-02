from __future__ import annotations

from application.utils import t, TBoolStr, TDesc, abstractmethod


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


class NameBasedResource:

    @classmethod
    @abstractmethod
    def get_by_name(cls, name: str) -> t.Optional[NameBasedResource]:
        pass


class URIBasedResource:

    @property
    @abstractmethod
    def claas_urn(self):
        pass

    @classmethod
    @abstractmethod
    def get_by_claas_urn(cls, urn: str):
        pass

    @staticmethod
    def claas_urn_separator() -> str:
        return ':'

    @classmethod
    @abstractmethod
    def dfl_claas_urn_builder(cls, *args, **kwargs) -> str:
        pass


nbr_type = t.Type[NameBasedResource]
ubr_type = t.Type[URIBasedResource]


__all__ = [
    'primitive_validate',
    'JSONSerializable',
    'NameBasedResource',
    'URIBasedResource',
    'nbr_type',
    'ubr_type',
]