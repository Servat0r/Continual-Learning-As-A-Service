"""
Authentication handling routes.
"""
from flask import Blueprint, request
from application.utils import *
from application.models import *
from application.errors import *
from http import HTTPStatus
from .tokens import token_auth
from application.validation import *


auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.post('/login/')
@auth_bp.post('/login')
def login():
    """
    Authentication token request (or retrieve).

    RequestSyntax:

    {
        "username": "<username>",
        "password": "<password>"
    }

    ResponseSyntax (on success):

    status: CREATED

    {
        "message": "Successful authentication.",
        "token": "<token_value>"
    }

    :return:
    """

    data, error, opts, extras = checked_json(request, False, {'username', 'password'})
    if error:
        if data:
            return error(**data)
        else:
            return error()

    username = data['username']
    password = data['password']

    result, msg = validate_username(username)
    if not result:
        return InvalidUsername(msg=msg)

    result, msg = validate_password(password)
    if not result:
        return InvalidPassword(msg=msg)

    user = User.get_by_name(username)
    if not user:
        return NotExistingUser(user=username)
    elif not user.check_correct_password(password):
        return InvalidPassword()
    token = user.get_token()
    return make_success_kwargs(HTTPStatus.OK, 'Successful authentication.', token=token)


@auth_bp.post('/logout/')
@auth_bp.post('/logout')
@token_auth.login_required
def logout():
    """
    Logouts the user.

    RequestSyntax: {}

    ResponseSyntax (on success):

    {
        "message": "Successfully logged out."
    }

    :return:
    """
    current_user = token_auth.current_user()
    current_user.revoke_token()
    return make_success_kwargs(HTTPStatus.OK, 'Successfully logged out.')


__all__ = [
    'token_auth',
    'auth_bp',
    'login',
    'logout',
]