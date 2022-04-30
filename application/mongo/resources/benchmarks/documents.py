from application.database import *
from application.mongo.resources.mongo_base_configs import *


class BenchmarkMetadata(MongoBaseMetadata):

    @classmethod
    def from_dict(cls, data: TDesc) -> t.Any:
        raise NotImplementedError


class MongoBenchmarkConfig(MongoResourceConfig):

    @staticmethod
    def meta_type() -> t.Type[BaseMetadata]:
        return BenchmarkMetadata

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type("Benchmark")

    def update(self, data, context):
        pass

    def __init__(self, *args, **values):
        super().__init__(*args, **values)