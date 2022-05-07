from application.database import *
from application.mongo.resources.mongo_base_configs import *


class StrategyMetadata(MongoBaseMetadata):
    pass


class MongoStrategyConfig(MongoResourceConfig):

    meta = {
        'indexes': [
            {'fields': ('owner', 'workspace', 'name'), 'unique': True}
        ]
    }

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type("Strategy")

    @staticmethod
    def meta_type() -> t.Type[BaseMetadata]:
        return StrategyMetadata

    def __init__(self, *args, **values):
        super().__init__(*args, **values)