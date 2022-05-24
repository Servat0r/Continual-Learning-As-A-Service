from flask import Blueprint, request

from application.utils import checked_json
from .auth import token_auth
from .resources import *


_DFL_CRITERION_NAME = "CLCriterion"


criterions_bp = Blueprint('criterions', __name__,
                          url_prefix='/users/<user:username>/workspaces/<workspace:wname>/criterions')


@criterions_bp.post('/')
@criterions_bp.post('')
@token_auth.login_required
def create_criterion(username, wname):
    return add_new_resource(username, wname, _DFL_CRITERION_NAME)


@criterions_bp.patch('/<resource:name>/')
@criterions_bp.patch('/<resource:name>')
@token_auth.login_required
def update_criterion(username, wname, name):
    data, error, opts, extras = checked_json(request, True)
    if error:
        if data:
            return error(**data)
        else:
            return error()
    else:
        return update_resource(username, wname, _DFL_CRITERION_NAME, name, data)


@criterions_bp.delete('/<resource:name>/')
@criterions_bp.delete('/<resource:name>')
@token_auth.login_required
def delete_criterion(username, wname, name):
    return delete_resource(username, wname, _DFL_CRITERION_NAME, name)


__all__ = [
    'criterions_bp',
    'create_criterion',
    'update_criterion',
    'delete_criterion',
]