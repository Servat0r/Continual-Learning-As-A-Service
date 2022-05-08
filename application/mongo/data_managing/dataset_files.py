from __future__ import annotations

from application.utils import t, TDesc
from application.database import db
from application.data_managing.base import BaseDatasetFile
from application.resources.contexts import ResourceContext
from application.mongo.mongo_base_metadata import *


class MongoDatasetFileMetadata(MongoBaseMetadata):
    pass


class MongoDatasetFile(BaseDatasetFile, db.EmbeddedDocument):

    # 1. Fields
    name = db.StringField()
    path = db.ListField(db.StringField())
    label = db.IntField()
    metadata = db.EmbeddedDocumentField(MongoDatasetFileMetadata)

    @classmethod
    def create(cls, name: str, subrepo: str, relative_path: str, context: ResourceContext, content: t.Any = None,
               is_binary: bool = True, save: bool = True):
        pass

    @classmethod
    def delete(cls, dfile: BaseDatasetFile):
        pass

    def get_data_repository(self):
        pass

    def read(self):
        pass

    def write(self, append=True):
        pass

    def get_relative_path(self) -> list[str]:
        return self.path

    def get_name(self) -> str:
        return self.name

    def get_label(self) -> int:
        return self.label

    def update(self, data: TDesc, save: bool = True) -> bool:
        pass

    def update_relative_path(self) -> bool:
        pass

    def update_name(self) -> bool:
        pass

    def update_label(self) -> bool:
        pass

    def to_dict(self) -> TDesc:
        pass


__all__ = [
    'MongoDatasetFileMetadata',
    'MongoDatasetFile',
]