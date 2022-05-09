from __future__ import annotations

from application.utils import t
from application.resources.base import DataType, BaseMetadata

from application.mongo.utils import RWLockableDocument
from application.mongo.mongo_base_metadata import MongoBaseMetadata
from application.mongo.resources.mongo_base_configs import *


class BenchmarkMetadata(MongoBaseMetadata):
    pass


class MongoBenchmarkConfig(MongoResourceConfig):

    _COLLECTION = 'benchmarks'

    meta = {
        'collection': _COLLECTION,
        'indexes': [
            {'fields': ('owner', 'workspace', 'name'), 'unique': True}
        ]
    }

    @staticmethod
    def meta_type() -> t.Type[BaseMetadata]:
        return BenchmarkMetadata

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type("Benchmark")

    def __init__(self, *args, **values):
        super().__init__(*args, **values)

    @property
    def parents(self) -> set[RWLockableDocument]:
        build_config = self.build_config

        has_data_repo = hasattr(build_config, 'data_repository')
        if has_data_repo:
            has_data_repo = (build_config.data_repository is not None)

        return {build_config.data_repository} if has_data_repo else super().parents


__all__ = [
    'BenchmarkMetadata',
    'MongoBenchmarkConfig',
]