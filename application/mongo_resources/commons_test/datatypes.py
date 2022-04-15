from __future__ import annotations
from application.mongo_resources.commons_test.base_datatypes import *
from application.mongo_resources.commons_test.documents import *


@DataType.set_resource_type()
class MongoDummy(Dummy):

    @classmethod
    def canonical_typename(cls) -> str:
        return Dummy.canonical_typename()

    @staticmethod
    def config_type() -> t.Type[MongoResourceConfig]:
        return MongoDummyDocument

    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.metadata: TDesc = {}

    def set_metadata(self, **kwargs):
        for item in kwargs.items():
            self.metadata[item[0]] = item[1]

    def get_metadata(self, key: str | None = None) -> TDesc | t.Any:
        if key is None:
            return self.metadata.copy()
        else:
            return self.metadata[key]

    def __repr__(self):
        return f"{type(self).__name__} ({super().__repr__()})."

    def __str__(self):
        return self.__repr__()


@DataType.set_resource_type()
class MongoSuperDummy(SuperDummy):

    @classmethod
    def canonical_typename(cls) -> str:
        return SuperDummy.canonical_typename()

    @staticmethod
    def config_type() -> t.Type[MongoResourceConfig]:
        return MongoSuperDummyDocument

    def __init__(self, name: str, desc: str, dummy: Dummy):
        super().__init__(name, desc, dummy)
        self.metadata: TDesc = {}

    def set_metadata(self, **kwargs):
        for item in kwargs.items():
            self.metadata[item[0]] = item[1]

    def get_metadata(self, key: str | None = None) -> TDesc | t.Any:
        if key is None:
            return self.metadata.copy()
        else:
            return self.metadata[key]

    def __repr__(self):
        return f"{type(self).__name__} ({super().__repr__()})."

    def __str__(self):
        return self.__repr__()