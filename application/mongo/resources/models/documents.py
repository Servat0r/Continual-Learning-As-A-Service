from __future__ import annotations

from application.utils import t, TBoolExc, auto_tboolexc
from application.resources.base import DataType, ReferrableDataType, BaseMetadata
from application.resources.contexts import UserWorkspaceResourceContext

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

    @auto_tboolexc
    def delete(self, context: UserWorkspaceResourceContext, locked=False, parents_locked=False) -> TBoolExc:
        with self.resource_delete(locked, parents_locked):
            OptimizerClass = t.cast(ReferrableDataType, DataType.get_type('CLOptimizer')).config_type()
            optimizers = OptimizerClass.get(build_config__model=self)
            for optimizer in optimizers:
                optimizer.delete(context, parents_locked=True)
            return super().delete(context, locked=True, parents_locked=True)


__all__ = [
    'ModelMetadata',
    'MongoModelConfig',
]