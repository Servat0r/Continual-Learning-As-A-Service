from application.mongo.resources import *


class DummyMetadata(BaseMetadata):

    @classmethod
    def from_dict(cls, data: TDesc) -> t.Any:
        raise NotImplementedError

    def to_dict(self) -> TDesc:
        result = super().to_dict()
        return result


class SuperDummyMetadata(BaseMetadata):

    @classmethod
    def from_dict(cls, data: TDesc) -> t.Any:
        raise NotImplementedError

    def to_dict(self) -> TDesc:
        result = super().to_dict()
        return result