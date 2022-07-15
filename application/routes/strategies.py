from flask import Blueprint
from http import HTTPStatus

from application.utils import *
from .auth import token_auth
from .resources import *


_DFL_STRATEGY_NAME_ = "Strategy"


strategies_bp = Blueprint('strategies', __name__,
                          url_prefix='/users/<user:username>/workspaces/<workspace:wname>/strategies')


@linker.args_rule(_DFL_STRATEGY_NAME_)
def strategy_args(strategy):
    username = strategy.get_owner().get_name()
    wname = strategy.get_workspace()
    name = strategy.get_name()
    return {
        'username': username,
        'wname': wname,
        'name': name,
    }


@strategies_bp.post('/')
@strategies_bp.post('')
@token_auth.login_required
def create_strategy(username, wname):
    return add_new_resource(username, wname, _DFL_STRATEGY_NAME_)


@strategies_bp.get('/<resource:name>/')
@strategies_bp.get('/<resource:name>')
@token_auth.login_required
@linker.link_rule(_DFL_STRATEGY_NAME_, blueprint=strategies_bp)
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
        data = linker.make_links(resource.to_dict())
        return make_success_dict(HTTPStatus.OK, data=data)


@strategies_bp.patch('/<resource:name>/')
@strategies_bp.patch('/<resource:name>')
@token_auth.login_required
@check_json(True, optionals={'name', 'description', 'build'})
def update_strategy(username, wname, name):
    """
    :param username:
    :param wname:
    :param name:
    :return:
    """
    data, opts, extras = get_check_json_data()
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