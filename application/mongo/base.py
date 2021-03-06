from __future__ import annotations

from application.utils import TBoolExc, abstractmethod
from application.models import User, Workspace
from application.mongo.locking import RWLockableDocument


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
               save: bool = True, parents_locked=False) -> MongoBaseUser | None:
        pass

    @abstractmethod
    def delete(self, locked=False, parents_locked=False) -> TBoolExc:
        pass


class MongoBaseWorkspace(Workspace, RWLockableDocument):

    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    @classmethod
    @abstractmethod
    def create(cls, name: str, owner: str | User, save: bool = True,
               open_on_create: bool = True, parents_locked=False) -> MongoBaseWorkspace | None:
        pass

    @abstractmethod
    def get_owner(self) -> MongoBaseUser:
        pass

    @abstractmethod
    def delete(self, parents_locked=False) -> TBoolExc:
        pass


__all__ = [
    'MongoBaseUser',
    'MongoBaseWorkspace',
]