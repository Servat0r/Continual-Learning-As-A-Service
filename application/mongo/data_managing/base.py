from __future__ import annotations

from application.data_managing.base import *
from application.mongo.base import *


class MongoBaseDataRepository(BaseDataRepository, RWLockableDocument):

    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    @classmethod
    @abstractmethod
    def create(cls, name: str, workspace: MongoBaseWorkspace, root: str = None,
               save: bool = True, parent_locked=False) -> BaseDataRepository | None:
        pass

    @abstractmethod
    def delete(self, locked=False, parent_locked=False) -> TBoolExc:
        pass

    @abstractmethod
    def get_workspace(self) -> MongoBaseWorkspace:
        pass

    @abstractmethod
    def get_owner(self) -> MongoBaseUser:
        pass