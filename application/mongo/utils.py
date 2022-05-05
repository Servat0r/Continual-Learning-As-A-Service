from __future__ import annotations
from application.database import *


class _SubResourceCtxManager:

    READ = 0
    WRITE = 1

    def __init__(self, resource: RWLockableDocument, create=False, lock_type=READ, locked=False):
        self.resource = resource
        self.create = create
        self.lock_type = lock_type
        self.locked = locked

    def __enter__(self):
        if self.create:
            self.resource.init_lock_set(wrlock=True, acquired=1)
        else:
            if not self.locked:
                if self.lock_type == self.READ:
                    self.resource.read_lock()
                elif self.lock_type == self.WRITE:
                    self.resource.write_lock()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.locked:
            if self.lock_type == self.READ:
                self.resource.read_unlock()
            elif self.lock_type == self.WRITE:
                self.resource.write_unlock()


class LockingError(Exception):

    _DFL_MSG = "Resource in use by another one."

    @classmethod
    def default(cls):
        return LockingError(cls._DFL_MSG)


class RWLockableDocument(db.Document):
    """
    A document that can be "read-write" locked.
    """
    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    rdlocks = db.IntField(default=0)
    wrlock = db.BooleanField(default=False)

    def __init__(self, *args, **values):
        super().__init__(*args, **values)
        self._acquired = 0

    def init_lock_set(self, rdlocks=0, wrlock=False, acquired=0):
        self.rdlocks = rdlocks
        self.wrlock = wrlock
        self._acquired = acquired

    def read_lock(self):
        result = self.modify({'wrlock': False}, inc__rdlocks=1)
        if result:
            self._acquired += 1
        else:
            raise LockingError.default()

    def write_lock(self):
        result = self.modify({'rdlocks': 0, 'wrlock': False}, wrlock=True)
        if result:
            self._acquired += 1
        else:
            raise LockingError.default()

    def read_unlock(self):
        if self._acquired > 0:
            self.modify({'wrlock': False}, inc__rdlocks=-1)
            self._acquired -= 1

    def write_unlock(self):
        if self._acquired > 0:
            self.modify({'rdlocks': 0, 'wrlock': True}, wrlock=False)
            self._acquired -= 1

    def resource_create(self, locked=False) -> _SubResourceCtxManager:
        return _SubResourceCtxManager(resource=self, create=True,
                                      lock_type=_SubResourceCtxManager.WRITE, locked=locked)

    def resource_delete(self, locked=False) -> _SubResourceCtxManager:
        return _SubResourceCtxManager(resource=self, create=False,
                                      lock_type=_SubResourceCtxManager.WRITE, locked=locked)

    def sub_resource_create(self, locked=False) -> _SubResourceCtxManager:
        return _SubResourceCtxManager(resource=self, create=False,
                                      lock_type=_SubResourceCtxManager.READ, locked=locked)

    def sub_resource_delete(self, locked=False) -> _SubResourceCtxManager:
        return _SubResourceCtxManager(resource=self, create=False,
                                      lock_type=_SubResourceCtxManager.READ, locked=locked)


class RWLockableEmbeddedDocument(db.EmbeddedDocument):
    """
    A document that can be "read-write" locked.
    """
    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    rdlocks = db.IntField(default=0)
    wrlock = db.BooleanField(default=False)

    def __init__(self, *args, **values):
        super().__init__(*args, **values)
        self._acquired = 0

    def init_lock_set(self, rdlocks=0, wrlock=False, acquired=0):
        self.rdlocks = rdlocks
        self.wrlock = wrlock
        self._acquired = acquired

    def read_lock(self):
        result = self.modify({'wrlock': False}, inc__rdlocks=1)
        if result:
            self._acquired += 1
        else:
            raise LockingError.default()

    def write_lock(self):
        result = self.modify({'rdlocks': 0, 'wrlock': False}, wrlock=True)
        if result:
            self._acquired += 1
        else:
            raise LockingError.default()

    def read_unlock(self):
        if self._acquired > 0:
            self.modify({'wrlock': False}, inc__rdlocks=-1)
            self._acquired -= 1

    def write_unlock(self):
        if self._acquired > 0:
            self.modify({'rdlocks': 0, 'wrlock': True}, wrlock=False)
            self._acquired -= 1

    def resource_create(self, locked=False) -> _SubResourceCtxManager:
        return _SubResourceCtxManager(resource=self, create=True,
                                      lock_type=_SubResourceCtxManager.WRITE, locked=locked)

    def resource_delete(self, locked=False) -> _SubResourceCtxManager:
        return _SubResourceCtxManager(resource=self, create=False,
                                      lock_type=_SubResourceCtxManager.WRITE, locked=locked)

    def sub_resource_create(self, locked=False) -> _SubResourceCtxManager:
        return _SubResourceCtxManager(resource=self, create=False,
                                      lock_type=_SubResourceCtxManager.READ, locked=locked)

    def sub_resource_delete(self, locked=False) -> _SubResourceCtxManager:
        return _SubResourceCtxManager(resource=self, create=False,
                                      lock_type=_SubResourceCtxManager.READ, locked=locked)