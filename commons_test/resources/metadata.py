from application.mongo.resources import *
from application.utils import TDesc


class DummyMetadata(MongoBaseMetadata):

    def to_dict(self) -> TDesc:
        result = super().to_dict()
        return result


class SuperDummyMetadata(MongoBaseMetadata):

    def to_dict(self) -> TDesc:
        result = super().to_dict()
        return result