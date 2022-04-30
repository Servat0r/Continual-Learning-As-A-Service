from __future__ import annotations
from application.resources.datatypes import *
from application.mongo.resources.mongo_base_configs import *
from .documents import *


@DataType.set_resource_type()
class MongoBenchmark(Benchmark):

    @staticmethod
    def config_type() -> t.Type[MongoResourceConfig]:
        return MongoBenchmarkConfig

    @classmethod
    def get_by_uri(cls, uri: str):
        return cls.config_type().get_by_uri(uri)

    @classmethod
    def dfl_uri_builder(cls, context: UserWorkspaceResourceContext, name: str) -> str:
        return cls.config_type().dfl_uri_builder(context, name)

    @classmethod
    def canonical_typename(cls) -> str:
        return Benchmark.canonical_typename()

    def __repr__(self):
        return f"{type(self).__name__} ({super().__repr__()})."

    def __str__(self):
        return self.__repr__()