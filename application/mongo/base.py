from __future__ import annotations
from abc import *
from datetime import datetime

from application import TDesc, TBoolStr, TBoolExc, t
from application.mongo.mongo_base_metadata import MongoBaseMetadata
from application.mongo.utils import RWLockableDocument
from application.models import User, Workspace


class MongoBaseUser(User, RWLockableDocument):

    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    @abstractmethod
    def workspaces(self) -> list[MongoBaseWorkspace]:
        pass

    @classmethod
    @abstractmethod
    def create(cls, username: str, email: str, password: str,
               save: bool = True, parent_locked=False) -> MongoBaseUser | None:
        pass

    @abstractmethod
    def delete(self, locked=False, parent_locked=False) -> TBoolExc:
        pass


class MongoBaseWorkspace(Workspace, RWLockableDocument):

    # TODO Aggiungere quando saranno pronti i DataRepository in quel modo
    """
    def data_repositories(self):
        pass
    """

    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    @classmethod
    @abstractmethod
    def create(cls, name: str, owner: str | User, save: bool = True,
               open_on_create: bool = True, parent_locked=False) -> MongoBaseWorkspace | None:
        pass

    @abstractmethod
    def get_owner(self) -> MongoBaseUser:
        pass

    @abstractmethod
    def delete(self, parent_locked=False) -> TBoolExc:
        pass