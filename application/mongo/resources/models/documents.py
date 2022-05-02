from application.database import *
from application.mongo.resources.mongo_base_configs import *


class ModelMetadata(MongoBaseMetadata):
    pass


class MongoModelConfig(MongoResourceConfig):

    meta = {
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