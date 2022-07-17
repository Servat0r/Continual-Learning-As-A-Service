from __future__ import annotations

from functools import wraps
from flask import Response, g
from flask_httpauth import HTTPTokenAuth

from application.utils import t
from application.models import check_token
from application.errors import *

token_auth = HTTPTokenAuth()


@token_auth.verify_token
def verify_token(token):
    g.missing_token = (len(token) == 0)
    return check_token(token)


@token_auth.error_handler
def token_auth_error(status):
    missing_token = g.pop('missing_token', False)
    return MissingToken(status=status) if missing_token else InvalidToken(status=status)


def check_current_user_ownership(username: str, msg: str = None, eval_args: dict[str, str] = None,
                                 msg_args: tuple = tuple(), msg_kwargs: dict = None,
                                 **func_kwargs) -> tuple[bool, t.Optional[Response]]:
    func_kwargs['username'] = username
    current_user = token_auth.current_user()
    msg_kwargs = msg_kwargs if msg_kwargs is not None else {}
    if current_user.username != username:
        msg = msg if msg is not None else ForbiddenOperation.dfl_msg
        if eval_args is not None:
            for arg_name, arg_val in eval_args.items():
                msg_kwargs[arg_name] = func_kwargs[arg_val]
        return False, ForbiddenOperation(msg.format(*msg_args, **msg_kwargs))
    else:
        return True, None


# Decorator for ownership checking!
def check_ownership(msg: str = None, eval_args: dict[str, str] = None, *msg_args, **msg_kwargs):
    def wrapper(f: t.Callable):
        @wraps(f)
        def new_f(username, *args, **kwargs):
            result, error = check_current_user_ownership(username, msg, eval_args, msg_args, msg_kwargs, **kwargs)
            if not result:
                return error
            return f(username, *args, **kwargs)
        return new_f
    return wrapper


def tuple_check_ownership(msg: str = None, eval_args: dict[str, str] = None, *msg_args, **msg_kwargs):
    def wrapper(f: t.Callable):
        @wraps(f)
        def new_f(username, *args, **kwargs):
            result, error = check_current_user_ownership(username, msg, eval_args, msg_args, msg_kwargs, **kwargs)
            if result:
                return f(username, *args, **kwargs)
            else:
                return None, error
        return new_f
    return wrapper


__all__ = [
    'token_auth',
    'verify_token',
    'token_auth_error',

    'check_current_user_ownership',
    'check_ownership',
    'tuple_check_ownership',
]