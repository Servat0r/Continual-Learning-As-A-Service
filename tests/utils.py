# Common utils for testcases
from __future__ import annotations

from typing import Sequence, Callable, TextIO
from http import HTTPStatus
from requests import Response

import sys
import time
import unittest
from functools import wraps

from application import MongoConfig

EMAIL = 'abc@example.com'
PASSWORD = '1234?abcD'
HOST = 'localhost'
PORT = 5000
DATABASE_NAME = 'test'


def time_measure(log_stream: TextIO = sys.stderr):
    def measurer(f: Callable):
        @wraps(f)
        def new_f(*args, **kwargs):
            elapsed = time.perf_counter()
            result = f(*args, **kwargs)
            elapsed = time.perf_counter() - elapsed
            print(f"Function execution time elapsed for {elapsed}", file=log_stream)
            return result
        return new_f
    return measurer


def default_app_run(app, host='0.0.0.0', port=5000):
    app.run(host=host, port=port)


def base_response_handler(response: Response, success_codes: int | Sequence[int] = HTTPStatus.OK):
    status_code = response.status_code
    reason = response.reason
    content_length = len(response.content)
    content = response.json() if content_length > 0 else ''
    print(status_code, reason, content, sep='\n')
    if not isinstance(success_codes, Sequence):
        success_codes: Sequence[int] = [success_codes]
    return True if status_code in success_codes else False


# Base MongoDB test config class
class BaseMongoTestConfig(MongoConfig):

    MONGODB_DB = 'test'
    MONGODB_HOST = HOST
    MONGODB_PORT = 27017
    MONGODB_CONNECT = False
    DATABASE_NAME = 'test'


# Base test case class
class BaseTestCase(unittest.TestCase):

    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    def assertBaseHandler(self, response: Response, success_codes: int | Sequence[int] = HTTPStatus.OK):
        self.assertTrue(base_response_handler(response, success_codes))


__all__ = [
    'HTTPStatus',
    'Sequence',
    'Response',

    'EMAIL',
    'PASSWORD',
    'HOST',
    'PORT',

    'time_measure',
    'base_response_handler',
    'BaseMongoTestConfig',
    'BaseTestCase',
]