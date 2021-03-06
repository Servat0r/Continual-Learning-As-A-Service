from __future__ import annotations

from application.utils import t

from application.resources.base import DataType
from application.resources.datatypes import Benchmark

from application.mongo.resources.mongo_base_configs import *
from .documents import *


@DataType.set_resource_type()
class MongoBenchmark(Benchmark):

    @staticmethod
    def config_type() -> t.Type[MongoResourceConfig]:
        return MongoBenchmarkConfig

    @classmethod
    def canonical_typename(cls) -> str:
        return Benchmark.canonical_typename()

    def __repr__(self):
        return f"{type(self).__name__} ({super().__repr__()})."

    def __str__(self):
        return self.__repr__()


__all__ = ['MongoBenchmark']