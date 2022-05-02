from application.database import *
from application.mongo.resources.mongo_base_configs import *


class StandardMetricSetMetadata(MongoBaseMetadata):
    pass


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

    def __init__(self, *args, **values):
        super().__init__(*args, **values)