from __future__ import annotations

from application.utils import TBoolStr, t, TDesc, abstractmethod
from application.database import db

from application.resources.contexts import ResourceContext
from application.resources.base import DataType

from application.mongo.data_managing import MongoDataRepository
from application.mongo.resources.mongo_base_configs import *


class MongoBaseBenchmarkBuildConfig(MongoBuildConfig):

    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    data_repository = db.ReferenceField(MongoDataRepository, default=None)

    @classmethod
    @abstractmethod
    def get_required(cls) -> set[str]:
        return (super(MongoBaseBenchmarkBuildConfig, cls) or set()).get_required()

    @classmethod
    @abstractmethod
    def get_optionals(cls) -> set[str]:
        return (super(MongoBaseBenchmarkBuildConfig, cls).get_optionals() or set()).union('data_repository')

    @abstractmethod
    def build(self, context: ResourceContext, locked=False, parents_locked=False):
        return super(MongoBaseBenchmarkBuildConfig, self).build(context, locked, parents_locked)


__all__ = [
    'MongoBaseBenchmarkBuildConfig',
]