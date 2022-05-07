import logging
import os
from logging.handlers import RotatingFileHandler

os.makedirs('logs', exist_ok=True)

file_handler = RotatingFileHandler(os.path.join('logs', 'auth_server.log'), maxBytes=10240,
                                   backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
file_handler.setLevel(logging.INFO)


__all__ = [
    'file_handler',
]