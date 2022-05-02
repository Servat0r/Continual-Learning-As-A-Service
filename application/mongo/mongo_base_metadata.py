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

    def get_created(self):
        return self.created

    def get_last_modified(self):
        return self.last_modified

    def update_last_modified(self, time: datetime = None):
        if time is None:
            time = datetime.utcnow()
        self.last_modified = time

    def __init__(self, *args, **kwargs):
        BaseMetadata.__init__(self)
        db.EmbeddedDocument.__init__(self, *args, **kwargs)