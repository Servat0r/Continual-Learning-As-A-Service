from __future__ import annotations
from abc import abstractmethod
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash
from application.resources import t, TDesc


def check_token(token):
    """
    Checks if given authentication token is associated to any user.
    :param token: Authentication token.
    :return: Corresponding user if present, None otherwise.
    """
    user = User.get_by_token(token)
    now = datetime.utcnow()
    if (user is not None) and (user.get_token_expiration() > now):
        return user
    else:
        return None


class User(UserMixin):

    __user_class__: t.Type[User] = None

    @staticmethod
    def check_ownership(username: str, user: User):
        return user.get_name() == username

    @staticmethod
    def set_user_class(cls: t.Type[User]):
        if User.__user_class__ is None:
            User.__user_class__ = cls
        return cls

    @staticmethod
    def user_class() -> t.Type[User] | None:
        return User.__user_class__

    def __str__(self):
        return self.__repr__()

    @abstractmethod
    def get_name(self):
        pass

    @abstractmethod
    def get_email(self):
        pass

    @abstractmethod
    def get_pw_hash(self):
        pass

    @abstractmethod
    def get_token_value(self):
        pass

    @abstractmethod
    def get_token_expiration(self):
        pass

    @abstractmethod
    def get_metadata(self) -> TDesc:
        pass

    @abstractmethod
    def workspaces(self):
        pass

    @abstractmethod
    def to_dict(self, include_email=False) -> TDesc:
        pass

    @classmethod
    @abstractmethod
    def get_by_token(cls, token: str) -> User:
        return User.user_class().get_by_token(token)

    @classmethod
    def canonicalize(cls, obj: str | User) -> User:
        if isinstance(obj, str):
            return cls.get_by_name(obj)
        elif isinstance(obj, User):
            return obj
        else:
            raise TypeError(f"Unsupported type: '{type(obj)}'.")

    @classmethod
    @abstractmethod
    def get_by_name(cls, name: str) -> User:
        return User.user_class().get_by_name(name)

    @classmethod
    @abstractmethod
    def get_by_email(cls, email: str) -> User:
        return User.user_class().get_by_email(email)

    @classmethod
    @abstractmethod
    def all(cls):
        return User.user_class().all()

    @classmethod
    @abstractmethod
    def create(cls, username: str, email: str = 'abc@example.com',
               password: str = '12345678', save: bool = True) -> User:
        return User.user_class().create(username, email, password, save)

    @abstractmethod
    def edit(self, data: dict, save: bool = True) -> dict[str, dict[str, str]]:
        pass

    @abstractmethod
    def delete(self):
        pass

    @abstractmethod
    def set_password(self, password: str, save: bool = True):
        """
        Sets the password for the current user.
        :param save:
        :param password:
        :return:
        """
        pass

    @staticmethod
    def get_password_hash(password: str) -> str:
        return generate_password_hash(password)

    @abstractmethod
    def check_correct_password(self, password):
        """
        Checks password for the current user against the memorized hash.
        :param password:
        :return:
        """
        pass

    @abstractmethod
    def avatar(self, size):
        """
        Returns a url for an avatar representation of the user.
        :param size:
        :return:
        """
        pass

    @abstractmethod
    def get_token(self, expires_in: int = 3600, save: bool = True):
        """
        Retrieves current used authentication token if present and not expiring soon, otherwise creates a new one.
        :param save:
        :param expires_in: Token lifetime in seconds.
        :return: Authentication token for current user.
        """
        pass

    @abstractmethod
    def revoke_token(self, save: bool = True):
        """
        Revokes current authentication token.
        :param save:
        :return:
        """
        pass


__all__ = [
    'check_token',
    'User',
]