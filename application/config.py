"""
Standard configuration examples.
"""
import os
from dotenv import load_dotenv

from .utils import t

basedir = os.path.abspath(os.getcwd())
load_dotenv(os.path.join(basedir, '.env'))

DFL_DATABASE_NAME = 'test_database'


_USE_DEFAULTS = True
bstr = os.environ.get("USE_DEFAULTS")
if bstr is not None:
    _USE_DEFAULTS = bool(int(bstr))


def get_env(key: str, default=None, transf: t.Callable = lambda x: x):
    if _USE_DEFAULTS:
        return default
    else:
        var = os.environ.get(key)
        if var is not None:
            return transf(var)
        else:
            return default


USE_MONGODB_AUTH = bool(get_env('USE_MONGODB_AUTH', 0, int))  # todo reset to false!


# Base configuration class for Flask app
class SimpleConfig(object):
    SECRET_KEY = get_env("SECRET_KEY", os.urandom(128))

    # For setting up an email notification service for failures
    MAIL_SERVER = get_env('MAIL_SERVER')
    MAIL_PORT = get_env('MAIL_PORT', 25, int)
    MAIL_USE_TLS = bool(get_env('MAIL_USE_TLS', 0, int))
    MAIL_USERNAME = get_env('MAIL_USERNAME')
    MAIL_PASSWORD = get_env('MAIL_PASSWORD')

    # Administrators email addresses
    ADMINS = [
        'servator.correnti@gmail.com',
        's.correnti@studenti.unipi.it',
    ]

    STD_FILESAVE_DIR = get_env("FILESAVE_DIR", os.path.join(basedir, '../files'))


# Configuration class for using a SQL database (e.g. PostgreSQL)
class SQLConfig(SimpleConfig):

    SQLALCHEMY_DATABASE_URI = get_env('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'app.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False


# Configuration for using MongoDB with MongoEngine
class MongoDefaultConfig(SimpleConfig):

    MONGODB_DB = get_env('MONGODB_DATABASE', DFL_DATABASE_NAME)
    MONGODB_HOST = get_env("MONGODB_HOSTNAME", 'localhost')
    MONGODB_PORT = get_env("MONGODB_PORT", 27017, int)

    MONGODB_CONNECT = bool(get_env("MONGODB_CONNECT", 0, int))  # TODO Change to False for "multi-service" Docker app!


class MongoAuthConfig(MongoDefaultConfig):

    MONGODB_USERNAME = get_env('MONGODB_USERNAME', 'user')
    MONGODB_PASSWORD = get_env('MONGODB_PASSWORD', 'password')


MongoConfig = MongoAuthConfig if USE_MONGODB_AUTH else MongoDefaultConfig

print(f"Use defaults: {_USE_DEFAULTS}")
print(f"Config class: {MongoConfig.__name__}")
tp = [(attr, getattr(MongoConfig, attr)) for attr in dir(MongoConfig) if not attr.startswith('__')]
print(*tp, sep='\n')


__all__ = [
    'get_env',
    'SimpleConfig',
    'SQLConfig',
    'MongoConfig',
    'DFL_DATABASE_NAME',
]