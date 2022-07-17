"""
User handling routes.
"""
from __future__ import annotations
from flask import Blueprint
from mongoengine import NotUniqueError
from http import HTTPStatus

from application.errors import *
from application.utils import *
from application.validation import *
from application.models import *
from .auth import *


_CHECK_DNS = bool(os.environ.get('EMAIL_VALIDATION_CHECK_DNS', False))

users_bp = Blueprint('users', __name__, url_prefix='/users')


@linker.args_rule('User')
def user_args(user: User):
    return {'username': user.get_name()}


@users_bp.post('/')
@users_bp.post('')
@check_json(False, required={'username', 'email', 'password'})
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
    data, opts, extras = get_check_json_data()
    username = data['username']
    email = data['email']
    password = data['password']

    result, msg = validate_username(username)
    if not result:
        return InvalidUsername(msg=msg)

    result, msg = validate_email(email, _CHECK_DNS)
    if not result:
        return InvalidEmail(msg=msg)

    result, msg = validate_password(password)
    if not result:
        return InvalidPassword(msg=msg)

    if User.get_by_name(username) is not None:
        return ExistingUser(user=username)
    elif User.get_by_email(email) is not None:
        return InvalidParameterValue(msg=f"Email '{email}' already in use.")
    else:
        user = User.create(username, email, password)
        if user:
            return make_success_kwargs(HTTPStatus.CREATED, msg=f"User '{user.get_name()}' correctly registered.")
        else:
            return InternalFailure(msg=f"Error when registering user.")


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
        return make_success_kwargs(HTTPStatus.NOT_FOUND, msg="No user registered.")
    else:
        data = {}
        for user in all_users:
            data[user.username] = linker.make_links(user.to_dict())
        return make_success_kwargs(HTTPStatus.OK, **data)


@users_bp.get('/<user:username>/')
@users_bp.get('/<user:username>')
@token_auth.login_required
@linker.link_rule('User', blueprint=users_bp)
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
        data = linker.make_links(user.to_dict(include_email=include_email))
        return make_success_dict(HTTPStatus.OK, data=data)


@users_bp.patch('/<user:username>/')
@users_bp.patch('/<user:username>')
@token_auth.login_required
@check_json(False, required=None, optionals={'username', 'email'})
@check_ownership(msg="You don't have permission to modify another user ({user}) profile", eval_args={'user': 'username'})
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

    data, opts, extras = get_check_json_data()

    if 'username' in opts:
        result, msg = validate_username(data['username'])
        if not result:
            return InvalidUsername(msg=msg)

    if 'email' in opts:
        email = data['email']
        result, msg = validate_email(email, _CHECK_DNS)
        if not result:
            return InvalidEmail(msg=msg)

    try:
        current_user = token_auth.current_user()
        result = current_user.edit(data)
        if len(result) == 0:
            return make_success_kwargs(HTTPStatus.NOT_MODIFIED)
        else:
            return make_success_kwargs(HTTPStatus.OK, msg=f"User {username} successfully updated.", **result)
    except NotUniqueError:
        return ForbiddenOperation(msg="Username or email are in use by another profile.")


@users_bp.patch('/<user:username>/password/')
@users_bp.patch('/<user:username>/password')
@token_auth.login_required
@check_json(False, required={'old_password', 'new_password'})
@check_ownership(msg="You cannot change another user's ({user}) password!", eval_args={'user': 'username'})
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

    data, opts, extras = get_check_json_data()
    current_user = token_auth.current_user()
    old_password = data['old_password']
    new_password = data['new_password']

    result, msg = validate_password(old_password)
    if not result:
        return InvalidPassword(msg=msg)

    result, msg = validate_password(new_password)
    if not result:
        return InvalidPassword(msg=msg)

    if not current_user.check_correct_password(old_password):
        return InvalidPassword(msg=f"Old password is incorrect.")
    elif old_password == new_password:
        return make_success_kwargs(HTTPStatus.NOT_MODIFIED)
    else:
        current_user.set_password(new_password)
        return make_success_kwargs(HTTPStatus.OK)


@users_bp.delete('/<user:username>/')
@users_bp.delete('/<user:username>')
@token_auth.login_required
@check_ownership(msg="You don't have the permission to delete another user ({user})!", eval_args={'user': 'username'})
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
    current_user = token_auth.current_user()
    result, exc = current_user.delete()
    if not result:
        return InternalFailure(msg=exc.args[0])
    else:
        return make_success_kwargs(
            HTTPStatus.OK,
            msg=f"User '{username}' successfully deleted.",
            username=username,
        )


__all__ = [
    'users_bp',
    'user_args',

    'register',
    'get_all_users',
    'get_user',
    'edit_user',
    'edit_password',
    'delete_user',
]