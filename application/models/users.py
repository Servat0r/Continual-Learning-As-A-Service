from __future__ import annotations
import os
import base64
from datetime import datetime, timedelta
from hashlib import md5
from mongoengine import NotUniqueError

from application.mongo_resources.mongo_base_metadata import BaseMetadata
from application.validation import USERNAME_MAX_CHARS
from application.database import db

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from resources import t, TDesc


def check_token(token):
    """
    Checks if given authentication token is associated to any user.
    :param token: Authentication token.
    :return: Corresponding user if present, None otherwise.
    """
    user = User.get_by_token(token)
    return user if (user is not None) and (user.token_expiration >= datetime.utcnow()) else None


class UserMetadata(BaseMetadata):

    def to_dict(self) -> TDesc:
        result = super().to_dict()
        return result

    @classmethod
    def from_dict(cls, data: TDesc) -> t.Any:
        raise NotImplementedError


class User(UserMixin, db.Document):

    username = db.StringField(required=True, max_length=USERNAME_MAX_CHARS, unique=True)
    email = db.StringField(required=True, unique=True)
    password_hash = db.StringField()
    token = db.StringField(unique=True)
    token_expiration = db.DateTimeField()
    metadata = db.EmbeddedDocumentField(UserMetadata)

    def __repr__(self):
        return f"<User '{self.username}'>"

    def __str__(self):
        return self.__repr__()

    def to_dict(self, include_email=False):
        data = {
            'id': str(self.id),
            'username': self.username,
            'metadata': self.metadata.to_dict(),
        }
        if include_email:
            data['email'] = self.email
        return data

    """
    def workspaces(self, to_list: bool = True):
        workspaces = Workspace.objects(owner=self)
        if to_list:
            return workspaces.all()
        else:
            return workspaces
    """

    @classmethod
    def get_by_token(cls, token: str) -> User:
        return cls.objects(token=token).first()

    @classmethod
    def canonicalize(cls, obj: str | User) -> User:
        if isinstance(obj, str):
            return User.get_by_name(obj)
        elif isinstance(obj, User):
            return obj
        else:
            raise TypeError(f"Unsupported type: '{type(obj)}'.")

    @classmethod
    def get_by_name(cls, name: str) -> User:
        return User.objects(username=name).first()

    @classmethod
    def get_by_email(cls, email: str) -> User:
        return User.objects(email=email).first()

    @classmethod
    def all(cls):
        return User.objects({}).all()

    @classmethod
    def create(cls, username: str, email: str = 'abc@example.com', password: str = '12345678', save: bool = True):
        now = datetime.utcnow()
        # noinspection PyArgumentList
        user = User(
            username=username,
            email=email,
            password_hash=cls.__get_password_hash(password),
            token='',
            token_expiration=now,
            metadata=UserMetadata(created=now, last_modified=now)
        )
        user.get_token(expires_in=-1, save=False)
        if save:
            user.save(force_insert=True)
            print(f"Created user '{username}' with id '{user.id}'")
        return user

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
            self.metadata.update_last_modified()

        if save:
            self.save()
        return result

    def delete(self):
        db.Document.delete(self)

    def set_password(self, password: str, save: bool = True):
        """
        Sets the password for the current user.
        :param save:
        :param password:
        :return:
        """
        self.password_hash = generate_password_hash(password)
        self.metadata.update_last_modified()
        if save:
            self.save()

    @staticmethod
    def __get_password_hash(password: str) -> str:
        return generate_password_hash(password)

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
        self.token_expiration = now + timedelta(seconds=expires_in)
        self.metadata.update_last_modified()
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
    'check_token',
    'User',
    'UserMetadata',
]