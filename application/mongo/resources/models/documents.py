from application.database import *
from application.mongo.resources.mongo_base_configs import *


class ModelMetadata(MongoBaseMetadata):

    @classmethod
    def from_dict(cls, data: TDesc) -> t.Any:
        raise NotImplementedError


class MongoModelConfig(MongoResourceConfig):

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type("Model")

    @staticmethod
    def meta_type() -> t.Type[BaseMetadata]:
        return ModelMetadata

    def update(self, data, context):
        pass

    def __init__(self, *args, **values):
        super().__init__(*args, **values)