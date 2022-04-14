from __future__ import annotations
from application.database import *
from application.mongo_resources.mongo_base_metadata import *
from application.models import *
from resources import *


class MongoBuildConfig(db.EmbeddedDocument, BuildConfig):

    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    @staticmethod
    @abstractmethod
    def target_type() -> t.Type[DataType]:
        pass

    @classmethod
    @abstractmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        pass

    @classmethod
    @abstractmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: ResourceContext, save: bool = True):
        pass

    @abstractmethod
    def build(self, context: ResourceContext):
        pass

    @abstractmethod
    def update(self, data, context: ResourceContext):
        pass

    @abstractmethod
    def delete(self, context: ResourceContext):
        pass


class MongoResourceConfig(db.Document, ResourceConfig):

    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    name = db.StringField(required=True)
    uri = db.StringField(required=True, unique=True)
    description = db.StringField(required=False)
    build_config = db.EmbeddedDocumentField(MongoBuildConfig)
    metadata = db.EmbeddedDocumentField(BaseMetadata)
    owner = db.ReferenceField(User)
    workspace = db.ReferenceField(Workspace)

    @classmethod
    @abstractmethod
    def get_by_uri(cls, uri: str):
        pass

    @classmethod
    @abstractmethod
    def dfl_uri_builder(cls, *args, **kwargs) -> str:
        pass

    @staticmethod
    @abstractmethod
    def target_type() -> t.Type[DataType]:
        pass

    @classmethod
    @abstractmethod
    def create(cls, data, context: ResourceContext, save: bool = True):
        pass

    @classmethod
    @abstractmethod
    def validate_input(cls, data, context: ResourceContext) -> TBoolStr:
        pass

    @abstractmethod
    def build(self, context: ResourceContext):
        pass

    @abstractmethod
    def update(self, data, context):
        pass

    def delete(self, context):
        db.Document.delete(self)

    def __init__(self, *args, **values):
        db.Document.__init__(self, *args, **values)