from __future__ import annotations

from application.utils import t
from application.resources.base import DataType, BaseMetadata
from application.mongo.mongo_base_metadata import MongoBaseMetadata
from application.mongo.resources.mongo_base_configs import *


class ModelMetadata(MongoBaseMetadata):
    pass


class MongoModelConfig(MongoResourceConfig):

    _COLLECTION = 'models'

    meta = {
        'collection': _COLLECTION,
        'indexes': [
            {'fields': ('owner', 'workspace', 'name'), 'unique': True}
        ]
    }

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type("Model")

    @staticmethod
    def meta_type() -> t.Type[BaseMetadata]:
        return ModelMetadata

    def __init__(self, *args, **values):
        super().__init__(*args, **values)


__all__ = [
    'ModelMetadata',
    'MongoModelConfig',
]