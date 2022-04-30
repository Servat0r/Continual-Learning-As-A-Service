"""
Standard configuration examples.
"""
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.getcwd())
load_dotenv(os.path.join(basedir, '.env'))

DFL_DATABASE_NAME = 'test_database'


# Base configuration class for Flask app
class SimpleConfig(object):
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(128)

    # For setting up an email notification service for failures
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = bool(os.environ.get('MAIL_USE_TLS') or False)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    # Administrators email addresses
    ADMINS = [
        'servator.correnti@gmail.com',
        's.correnti@studenti.unipi.it',
    ]

    STD_FILESAVE_DIR = os.environ.get("FILESAVE_DIR") or os.path.join(basedir, '../files')


# Configuration class for using a SQL database (e.g. PostgreSQL)
class SQLConfig(SimpleConfig):

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


# Configuration for using MongoDB with MongoEngine
class MongoConfig(SimpleConfig):

    MONGODB_DB = os.environ.get("MONGODB_DATABASE") or DFL_DATABASE_NAME
    MONGODB_HOST = os.environ.get("MONGODB_HOST") or 'localhost'
    MONGODB_PORT = os.environ.get("MONGODB_PORT") or 27017
    MONGODB_CONNECT = os.environ.get("MONGODB_CONNECT") or True  # TODO Change to False for "multi-service" Docker app!


__all__ = [
    'SimpleConfig',
    'SQLConfig',
    'MongoConfig',
    'DFL_DATABASE_NAME',
]