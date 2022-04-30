from __future__ import annotations
import os
import base64
from datetime import datetime, timedelta
from hashlib import md5
from werkzeug.security import check_password_hash
from mongoengine import NotUniqueError

from application.mongo.mongo_base_metadata import MongoBaseMetadata
from application.validation import USERNAME_MAX_CHARS
from application.database import db
from application.resources import t, TDesc
from application.models import User, Workspace


class UserMetadata(MongoBaseMetadata):

    def to_dict(self) -> TDesc:
        result = super().to_dict()
        return result

    @classmethod
    def from_dict(cls, data: TDesc) -> t.Any:
        raise NotImplementedError


@User.set_user_class
class MongoUser(User, db.Document):

    username = db.StringField(required=True, max_length=USERNAME_MAX_CHARS, unique=True)
    email = db.StringField(required=True, unique=True)
    password_hash = db.StringField()
    token = db.StringField(unique=True)
    token_expiration = db.DateTimeField()
    metadata = db.EmbeddedDocumentField(UserMetadata)

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

    def workspaces(self):
        return Workspace.get_class().get_by_owner(self)

    def __repr__(self):
        return f"<User '{self.username}'>"

    def to_dict(self, include_email=False):
        data = {
            'username': self.username,
            'metadata': self.metadata.to_dict(),
        }
        if include_email:
            data['email'] = self.email
        return data

    @classmethod
    def get_by_token(cls, token: str) -> User:
        return cls.objects(token=token).first()

    @classmethod
    def get_by_name(cls, name: str) -> User:
        return cls.objects(username=name).first()

    @classmethod
    def get_by_email(cls, email: str) -> User:
        return cls.objects(email=email).first()

    @classmethod
    def all(cls):
        return cls.objects({}).all()

    @classmethod
    def create(cls, username: str, email: str = 'abc@example.com', password: str = '12345678', save: bool = True):
        now = datetime.utcnow()
        # noinspection PyArgumentList
        user = cls(
            username=username,
            email=email,
            password_hash=cls.get_password_hash(password),
            token='',
            token_expiration=now,
            metadata=UserMetadata(created=now, last_modified=now)
        )
        user.get_token(expires_in=3600, save=False)
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

    def check_correct_password(self, password):
        """
        Checks password for the current user against the memorized hash.
        :param password:
        :return:
        """
        return check_password_hash(self.password_hash, password)

    def set_password(self, password: str, save: bool = True):
        """
        Sets the password for the current user.
        :param save:
        :param password:
        :return:
        """
        self.password_hash = self.get_password_hash(password)
        self.metadata.update_last_modified()
        if save:
            self.save()

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