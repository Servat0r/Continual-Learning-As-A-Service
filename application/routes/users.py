"""
User handling routes.
"""
from __future__ import annotations
from flask import Blueprint, request
from mongoengine import NotUniqueError
from http import HTTPStatus

from application.errors import *
from application.utils import *
from application.validation import *
from application.models import *
from application.routes.auth import token_auth

_CHECK_DNS = bool(os.environ.get('EMAIL_VALIDATION_CHECK_DNS') or False)

users_bp = Blueprint('users', __name__, url_prefix='/users')


# Utils
def check_ownership(username, msg: str = None, *args, **kwargs) -> tuple[bool, ServerResponseError | None]:
    current_user = token_auth.current_user()
    if current_user.username != username:
        return False, ForbiddenOperation(msg.format(*args, **kwargs))
    else:
        return True, None


@users_bp.app_errorhandler(HTTPStatus.INTERNAL_SERVER_ERROR)
def internal_server_error(error):
    print(type(error))
    return InternalFailure(str(error))


@users_bp.app_errorhandler(HTTPStatus.SERVICE_UNAVAILABLE)
def service_unavailable(error):
    print(type(error))
    return ServiceUnavailable(str(error))


@users_bp.post('/')
@users_bp.post('')
def register():
    """
    Registers a new user.

    RequestSyntax:

    {
        "username": "<username>",
        "email": "<email>",
        "password": "<password>"
    }

    ResponseSyntax (on success):
    status: CREATED

    {
        "message": "User <username> successfully registered."
    }

    :return:
    """

    data, error, opts, extras = checked_json(request, False, {'username', 'email', 'password'})
    if error:
        if data:
            return error(**data)
        else:
            return error()
    else:
        username = data['username']
        email = data['email']
        password = data['password']

        result, msg = validate_username(username)
        if not result:
            return InvalidUsername(msg)

        result, msg = validate_email(email, _CHECK_DNS)
        if not result:
            return InvalidEmail(msg)

        result, msg = validate_password(password)
        if not result:
            return InvalidPassword(msg)

        if User.get_by_name(username) is not None:
            return ExistingUser(user=username)
        elif User.get_by_email(email) is not None:
            return InvalidParameterValue(msg=f"Email '{email}' already in use.")
        else:
            user = User.create(username, email, password)
            if user:
                return make_success_kwargs(HTTPStatus.CREATED, f"User '{user.get_name()}' correctly registered.")
            else:
                return InternalFailure(f"Error when registering user.")


@users_bp.get('/')
@users_bp.get('')
@token_auth.login_required
def get_all_users():
    """
    Retrieves all users.

    RequestSyntax: {}

    ResponseSyntax (on success):

    {
        "message": "Request successfully completed.",
        "<username1>": "<user_json>",
        "<username2>": "<user_json>",
        ...
    }

    :return:
    """

    all_users = User.all()
    if len(all_users) == 0:
        return make_success_kwargs(HTTPStatus.NO_CONTENT, "No user registered.")
    else:
        data = {}
        for user in all_users:
            data[user.username] = user.to_dict()
        return make_success_kwargs(HTTPStatus.OK, **data)


@users_bp.get('/<user:username>/')
@users_bp.get('/<user:username>')
@token_auth.login_required
def get_user(username):
    """
    Retrieves a user.

    RequestSyntax: {}

    ResponseSyntax (on success):
    {
        "message": "Request successfully completed.",
        <user_json>
    }

    :param username: Username.
    :return:
    """

    current_user = token_auth.current_user()
    user = User.get_by_name(username)
    if not user:
        return NotExistingUser(user=username)
    else:
        include_email = (current_user.username == username)
        return make_success_dict(HTTPStatus.OK, user.to_dict(include_email=include_email))


@users_bp.patch('/<user:username>/')
@users_bp.patch('/<user:username>')
@token_auth.login_required
def edit_user(username):
    """
    Edits username/email.

    RequestSyntax:

    {
        ["username": "<new_username>"],
        ["email": "<new_email>"]
    }

    ResponseSyntax (on success):

    {
        ["username": {
            "before": "<old_username>",
            "after": "<after_username>"
        }],
        ["email": {
            "before": "<old_email>",
            "after": "<after_email>"
        }]
    }

    :param username:
    :return:
    """

    data, error, opts, extras = checked_json(request, False, required=None, optionals={'username', 'email'})
    if error:
        if data:
            return error(**data)
        else:
            return error()

    hasUsername = False
    email = ''

    if 'username' in opts:
        hasUsername = True
        result, msg = validate_username(data['username'])
        if not result:
            return InvalidUsername(msg)

    if 'email' in opts:
        email = data['email']
        result, msg = validate_email(email, _CHECK_DNS)
        if not result:
            return InvalidEmail(msg)

    current_user = token_auth.current_user()
    if (hasUsername and current_user.username != username) or ((not hasUsername) and current_user.email != email):
        return ForbiddenOperation("You don't have permission to modify another user profile, either because your"
                                  " username or your email or both do not match.")
    else:
        try:
            result = current_user.edit(data)
            if len(result) == 0:
                return make_success_kwargs(HTTPStatus.NOT_MODIFIED)
            else:
                return make_success_kwargs(HTTPStatus.OK, f"User {username} successfully updated.", **result)
        except NotUniqueError as nue:
            print(nue)
            return ForbiddenOperation("Username or email are in use by another profile.")


@users_bp.patch('/<user:username>/password/')
@users_bp.patch('/<user:username>/password')
@token_auth.login_required
def edit_password(username):
    """
    Edits user password.

    RequestSyntax:

    {
        "old_password": "<old_password>",
        "new_password": "<new_password>"
    }

    ResponseSyntax (on success): {
        "message": "Request successfully completed."
    }

    :param username: Username.
    :return:
    """
    result, error = check_ownership(username, "You cannot change another user's password!")
    if not result:
        return error

    data, error, opts, extras = checked_json(request, False, {'old_password', 'new_password'})
    if error:
        if data:
            return error(**data)
        else:
            return error()
    else:
        current_user = token_auth.current_user()
        old_password = data['old_password']
        new_password = data['new_password']

        result, msg = validate_password(old_password)
        if not result:
            return InvalidPassword(msg)

        result, msg = validate_password(new_password)
        if not result:
            return InvalidPassword(msg)

        if not current_user.check_correct_password(old_password):
            return InvalidPassword(f"Old password is incorrect.")
        elif old_password == new_password:
            return make_success_kwargs(HTTPStatus.NOT_MODIFIED)
        else:
            current_user.set_password(new_password)
            return make_success_kwargs(HTTPStatus.OK)


@users_bp.delete('/<user:username>/')
@users_bp.delete('/<user:username>')
@token_auth.login_required
def delete_user(username):
    """
    Deletes user.

    RequestSyntax: {}

    ResponseSyntax (on success):

    {
        "message": "User <username> successfully deleted.",
        "username": "<username>"
    }

    :param username:
    :return:
    """
    result, error = check_ownership(username, "You don't have the permission to delete another user!")
    if not result:
        return error

    current_user = token_auth.current_user()
    if current_user.username == username:
        result, msg = User.delete(current_user)
        if not result:
            return InternalFailure(msg=msg)
        else:
            return make_success_kwargs(HTTPStatus.OK, msg=f"User '{username}' successfully deleted.", username=username)
    else:
        return ForbiddenOperation("You don't have the permission to delete another user!")


__all__ = [
    'users_bp',
    'check_ownership',
    'internal_server_error',
    'service_unavailable',

    'register',
    'get_all_users',
    'get_user',
    'edit_user',
    'edit_password',
    'delete_user',
]