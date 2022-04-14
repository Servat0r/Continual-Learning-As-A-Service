from datetime import datetime
from application.database import db
from resources import *


class BaseMetadata(JSONSerializable, db.EmbeddedDocument):

    def to_dict(self) -> TDesc:
        return {
            'created': self.created,
            'last_modified': self.last_modified,
        }

    @classmethod
    def from_dict(cls, data: TDesc) -> t.Any:
        raise NotImplementedError

    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }
    created = db.DateTimeField(required=True)
    last_modified = db.DateTimeField(required=True)

    def update_last_modified(self, time=datetime.utcnow()):
        self.last_modified = time