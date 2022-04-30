from datetime import datetime
from application.database import db
from application.resources import *


class MongoBaseMetadata(BaseMetadata, db.EmbeddedDocument):

    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    created = db.DateTimeField(required=True)
    last_modified = db.DateTimeField(required=True)

    @classmethod
    def from_dict(cls, data: TDesc) -> t.Any:
        raise NotImplementedError

    def get_created(self):
        return self.created

    def get_last_modified(self):
        return self.last_modified

    def set_last_modified(self, time):
        self.last_modified = time

    def __init__(self, *args, **kwargs):
        BaseMetadata.__init__(self)
        db.EmbeddedDocument.__init__(self, *args, **kwargs)