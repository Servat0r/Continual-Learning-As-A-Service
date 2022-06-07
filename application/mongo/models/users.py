from __future__ import annotations
import base64
from datetime import datetime, timedelta
from hashlib import md5
from werkzeug.security import check_password_hash
from mongoengine import NotUniqueError

from application.utils import TDesc, TBoolExc, os
from application.validation import USERNAME_MAX_CHARS
from application.database import db
from application.models import User, Workspace

from application.mongo.base import *
from application.mongo.mongo_base_metadata import MongoBaseMetadata

from application.data_managing import BaseDataManager
from application.mongo.locking import RWLockableDocument


class UserMetadata(MongoBaseMetadata):
    pass


@User.set_user_class
class MongoUser(MongoBaseUser):

    # 1. Fields
    _COLLECTION = 'users'

    meta = {
        'collection': _COLLECTION,
    }

    username = db.StringField(required=True, max_length=USERNAME_MAX_CHARS, unique=True)
    email = db.StringField(required=True, unique=True)
    password_hash = db.StringField()
    token = db.StringField(unique=True)
    token_expiration = db.DateTimeField()
    metadata = db.EmbeddedDocumentField(UserMetadata)

    @property
    def parents(self) -> set[RWLockableDocument]:
        return set()

    # 3. General classmethods
    @classmethod
    def get(cls, username: str | None = None, **kwargs) -> list[MongoBaseUser]:
        if username is not None:
            kwargs['username'] = username
        return list(cls.objects(**kwargs).all())

    @classmethod
    def all(cls):
        return cls.get()

    @classmethod
    def get_by_name(cls, name: str) -> MongoBaseUser | None:
        result = cls.get(name)
        return result[0] if len(result) >= 1 else None

    @classmethod
    def get_by_email(cls, email: str) -> MongoBaseUser | None:
        result = cls.get(email=email)
        return result[0] if len(result) >= 1 else None

    @classmethod
    def get_by_token(cls, token: str) -> MongoBaseUser | None:
        result = cls.get(token=token)
        return result[0] if len(result) >= 1 else None

    # 4. Create + callbacks
    @classmethod
    def create(cls, username: str, email: str, password: str,
               save: bool = True, parents_locked=False) -> MongoBaseUser | None:
        now = datetime.utcnow()
        # noinspection PyArgumentList
        user = cls(
            username=username,
            email=email,
            password_hash=cls.get_password_hash(password),
            token='',
            token_expiration=now,
            metadata=UserMetadata(created=now, last_modified=now),
        )
        if user is not None:
            with user.resource_create():
                user.get_token(expires_in=172800, save=False)
                if save:
                    user.save(create=True)
                    print(f"Created user '{username}' with id '{user.id}'")
                    manager = BaseDataManager.get()
                    manager.create_subdir(user.user_base_dir())

        return user

    # 5. Delete + callbacks
    def delete(self, locked=False, parents_locked=False) -> TBoolExc:
        with self.resource_delete(locked=locked, parents_locked=parents_locked):
            try:
                for workspace in self.workspaces():
                    workspace.close()
                    workspace.delete(parents_locked=True)

                db.Document.delete(self)
                manager = BaseDataManager.get()
                manager.remove_subdir(self.user_base_dir())
                return True, None
            except Exception as ex:
                return False, ex

    # 6. Read/Update/General instance methods
    def __repr__(self):
        return f"User <{self.username}>"

    def get_name(self):
        return self.username

    def get_email(self):
        return self.email

    def get_pw_hash(self):
        return self.password_hash

    def get_token_value(self):
        return self.token

    def get_token_expiration(self):
        return self.token_expiration

    def get_metadata(self) -> TDesc:
        return self.metadata.to_dict()

    def edit(self, data: dict, save: bool = True) -> dict[str, dict[str, str]]:
        username = data.pop('username')
        email = data.pop('email')
        result = {}
        modified = False

        if (self.username != username) and (username is not None):
            modified = True
            before_username = self.username
            self.username = username
            result['username'] = {'before': before_username, 'after': username}

        if (self.email != email) and (email is not None):
            modified = True
            before_email = self.email
            self.email = email
            result['email'] = {'before': before_email, 'after': email}

        if modified:
            print(f"User {self.username} modified")
            self.update_last_modified(save=save)

        if save:
            self.save()
        return result

    def save(self, create=False) -> bool:
        try:
            if create:
                db.Document.save(self, force_insert=True)
            else:
                self.update_last_modified(save=False)
                db.Document.save(self, save_condition={'id': self.id})
            return True
        except Exception as ex:
            return False

    def set_password(self, password: str, save: bool = True):
        """
        Sets the password for the current user.
        :param save:
        :param password:
        :return:
        """
        self.password_hash = self.get_password_hash(password)
        self.update_last_modified(save=save)
        if save:
            self.save()

    def user_base_dir(self):
        return f"User_{self.get_id()}"

    def update_last_modified(self, time: datetime = None, save: bool = True):
        self.metadata.update_last_modified(time)
        if save:
            self.save()

    def to_dict(self, include_email=False):
        data = {
            'username': self.username,
            'metadata': self.metadata.to_dict(),
        }
        if include_email:
            data['email'] = self.email
        return data

    # 7. Query-like Instance methods
    def workspaces(self):
        return Workspace.get_class().get_by_owner(self) or []

    # 9. Special methods
    def check_correct_password(self, password):
        """
        Checks password for the current user against the memorized hash.
        :param password:
        :return:
        """
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        """
        Returns a url for an avatar representation of the user.
        :param size:
        :return:
        """
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def get_token(self, expires_in: int = 3600, save: bool = True):
        """
        Retrieves current used authentication token if present and not expiring soon, otherwise creates a new one.
        :param save:
        :param expires_in: Token lifetime in seconds.
        :return: Authentication token for current user.
        """
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        while True:
            try:
                self.token = base64.b64encode(os.urandom(96)).decode('utf-8')  # 96 * 4/3 == 128
                break
            except NotUniqueError:
                continue
        now = datetime.utcnow()
        self.token_expiration = now + timedelta(seconds=expires_in)
        self.update_last_modified(save=save)
        if save:
            self.save()
        return self.token

    def revoke_token(self, save: bool = True):
        """
        Revokes current authentication token.
        :param save:
        :return:
        """
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)
        if save:
            self.save()


__all__ = [
    'UserMetadata',
    'MongoUser',
]