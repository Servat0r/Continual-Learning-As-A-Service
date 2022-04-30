from application.database import *
from application.mongo.resources.mongo_base_configs import *


class StandardMetricSetMetadata(MongoBaseMetadata):

    @classmethod
    def from_dict(cls, data: TDesc) -> t.Any:
        raise NotImplementedError


class MongoStandardMetricSetConfig(MongoResourceConfig):

    meta = {
        'indexes': [
            {'fields': ('owner', 'workspace', 'name'), 'unique': True}
        ]
    }

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type("StandardMetricSet")

    @staticmethod
    def meta_type() -> t.Type[BaseMetadata]:
        return StandardMetricSetMetadata

    def update(self, data, context):
        pass

    def __init__(self, *args, **values):
        super().__init__(*args, **values)