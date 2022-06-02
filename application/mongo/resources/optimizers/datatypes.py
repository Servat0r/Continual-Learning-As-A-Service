from __future__ import annotations

from application.utils import t

from application.resources.contexts import UserWorkspaceResourceContext
from application.resources.base import DataType
from application.resources.datatypes import CLOptimizer

from application.mongo.resources.mongo_base_configs import *
from .documents import *


@DataType.set_resource_type()
class MongoCLOptimizer(CLOptimizer):

    @staticmethod
    def config_type() -> t.Type[MongoResourceConfig]:
        return MongoCLOptimizerConfig

    @classmethod
    def get_by_claas_urn(cls, urn: str):
        return cls.config_type().get_by_claas_urn(urn)

    @classmethod
    def dfl_claas_urn_builder(cls, context: UserWorkspaceResourceContext, name: str) -> str:
        return cls.config_type().dfl_claas_urn_builder(context, name)

    @classmethod
    def canonical_typename(cls) -> str:
        return CLOptimizer.canonical_typename()

    def __repr__(self):
        return f"{type(self).__name__} ({super().__repr__()})."

    def __str__(self):
        return self.__repr__()


__all__ = ['MongoCLOptimizer']