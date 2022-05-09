"""
Standard configuration examples.
"""
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.getcwd())
load_dotenv(os.path.join(basedir, '.env'))

DFL_DATABASE_NAME = 'test_database'

_USE_DEFAULTS = os.environ.get("USE_DEFAULTS", True)


def get_env(key: str, default=None):
    return default if _USE_DEFAULTS else os.environ.get(key, default)


USE_MONGODB_AUTH = bool(get_env('USE_MONGODB_AUTH', False))


# Base configuration class for Flask app
class SimpleConfig(object):
    SECRET_KEY = get_env("SECRET_KEY", os.urandom(128))

    # For setting up an email notification service for failures
    MAIL_SERVER = get_env('MAIL_SERVER')
    MAIL_PORT = int(get_env('MAIL_PORT', 25))
    MAIL_USE_TLS = bool(get_env('MAIL_USE_TLS', False))
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
    MONGODB_PORT = get_env("MONGODB_PORT", 27017)

    MONGODB_CONNECT = get_env("MONGODB_CONNECT", True)  # TODO Change to False for "multi-service" Docker app!


class MongoAuthConfig(MongoDefaultConfig):

    MONGODB_USERNAME = get_env('MONGODB_USERNAME', 'user')
    MONGODB_PASSWORD = get_env('MONGODB_PASSWORD', 'password')


MongoConfig = MongoAuthConfig if USE_MONGODB_AUTH else MongoDefaultConfig


__all__ = [
    'get_env',
    'SimpleConfig',
    'SQLConfig',
    'MongoConfig',
    'DFL_DATABASE_NAME',
]