from flask import Response
from flask_httpauth import HTTPTokenAuth

from application.utils import t
from application.models import check_token
from application.errors import *

token_auth = HTTPTokenAuth()


@token_auth.verify_token
def verify_token(token):
    return check_token(token)


@token_auth.error_handler
def token_auth_error(status):
    return make_error(status, 'Your authentication token is invalid or expired.')


def check_current_user_ownership(username: str, msg: str = None, *args, **kwargs) -> tuple[bool, t.Optional[Response]]:
    current_user = token_auth.current_user()
    if current_user.username != username:
        msg = msg if msg is not None else ForbiddenOperation.dfl_msg
        return False, ForbiddenOperation(msg.format(*args, **kwargs))
    else:
        return True, None


__all__ = [
    'token_auth',
    'verify_token',
    'token_auth_error',
    'check_current_user_ownership',
]