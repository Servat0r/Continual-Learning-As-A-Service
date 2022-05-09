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
        return super().get_required()

    @classmethod
    @abstractmethod
    def get_optionals(cls) -> set[str]:
        return super().get_optionals().union('data_repository')


__all__ = [
    'MongoBaseBenchmarkBuildConfig',
]