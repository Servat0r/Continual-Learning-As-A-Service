from application.database import *
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