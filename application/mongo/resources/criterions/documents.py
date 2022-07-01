from __future__ import annotations

from application.utils import t, TBoolExc
from application.resources.contexts import UserWorkspaceResourceContext
from application.resources.base import DataType, ReferrableDataType, BaseMetadata

from application.mongo.mongo_base_metadata import MongoBaseMetadata
from application.mongo.resources.mongo_base_configs import *


class CLCriterionMetadata(MongoBaseMetadata):
    pass


class MongoCLCriterionConfig(MongoResourceConfig):

    _COLLECTION = 'criterions'

    meta = {
        'collection': _COLLECTION,
        'indexes': [
            {'fields': ('owner', 'workspace', 'name'), 'unique': True}
        ]
    }

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type("CLCriterion")

    @staticmethod
    def meta_type() -> t.Type[BaseMetadata]:
        return CLCriterionMetadata

    def __init__(self, *args, **values):
        super().__init__(*args, **values)

    def delete(self, context: UserWorkspaceResourceContext, locked=False, parents_locked=False) -> TBoolExc:
        with self.resource_delete(locked, parents_locked):
            try:
                StrategyClass = t.cast(ReferrableDataType, DataType.get_type('Strategy')).config_type()
                strategies = StrategyClass.get(build_config__criterion=self)
                for strategy in strategies:
                    strategy.delete(context, parents_locked=True)
                return super().delete(context, locked=True, parents_locked=True)
            except Exception as ex:
                return False, ex


__all__ = [
    'CLCriterionMetadata',
    'MongoCLCriterionConfig',
]