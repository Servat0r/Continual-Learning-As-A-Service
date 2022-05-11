from __future__ import annotations

from application.utils import abstractmethod, TBoolExc
from application.data_managing.base import BaseDataRepository

from application.mongo.utils import RWLockableDocument
from application.mongo.base import MongoBaseWorkspace, MongoBaseUser


class MongoBaseDataRepository(BaseDataRepository, RWLockableDocument):

    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    @classmethod
    @abstractmethod
    def create(cls, name: str, workspace: MongoBaseWorkspace, root: str = None, desc: str = None,
               save: bool = True, parents_locked=False) -> BaseDataRepository | None:
        pass

    @abstractmethod
    def delete(self, locked=False, parents_locked=False) -> TBoolExc:
        pass

    @abstractmethod
    def get_workspace(self) -> MongoBaseWorkspace:
        pass

    @abstractmethod
    def get_owner(self) -> MongoBaseUser:
        pass


__all__ = ['MongoBaseDataRepository']