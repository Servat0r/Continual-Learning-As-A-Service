from flask import Blueprint, request
from http import HTTPStatus

from application.utils import checked_json, make_success_dict
from .auth import token_auth
from .resources import *


_DFL_STRATEGY_NAME_ = "Strategy"


strategies_bp = Blueprint('strategies', __name__,
                          url_prefix='/users/<user:username>/workspaces/<workspace:wname>/strategies')


@strategies_bp.post('/')
@strategies_bp.post('')
@token_auth.login_required
def create_strategy(username, wname):
    return add_new_resource(username, wname, _DFL_STRATEGY_NAME_)


@strategies_bp.get('/<resource:name>/')
@strategies_bp.get('/<resource:name>')
@token_auth.login_required
def get_strategy(username, wname, name):
    """
    :param username:
    :param wname:
    :param name:
    :return:
    """
    resource, response = get_resource(username, wname, _DFL_STRATEGY_NAME_, name=name)
    if response is not None:    # error
        return response
    else:
        return make_success_dict(HTTPStatus.OK, resource.to_dict())


@strategies_bp.patch('/<resource:name>/')
@strategies_bp.patch('/<resource:name>')
@token_auth.login_required
def update_strategy(username, wname, name):
    """
    :param username:
    :param wname:
    :param name:
    :return:
    """
    data, error, opts, extras = checked_json(request, True)
    if error:
        if data:
            return error(**data)
        else:
            return error()
    else:
        return update_resource(username, wname, _DFL_STRATEGY_NAME_, name, data)


@strategies_bp.delete('/<resource:name>/')
@strategies_bp.delete('/<resource:name>')
@token_auth.login_required
def delete_strategy(username, wname, name):
    return delete_resource(username, wname, _DFL_STRATEGY_NAME_, name)


__all__ = [
    'strategies_bp',
    'create_strategy',
    'get_strategy',
    'update_strategy',
    'delete_strategy',
]