from flask import Blueprint
from http import HTTPStatus

from application.utils import *
from .auth import token_auth
from .resources import *


_DFL_OPTIM_NAME_ = "CLOptimizer"


optimizers_bp = Blueprint('optimizers', __name__,
                          url_prefix='/users/<user:username>/workspaces/<workspace:wname>/optimizers')


@linker.args_rule(_DFL_OPTIM_NAME_)
def optimizer_args(optimizer):
    username = optimizer.get_owner().get_name()
    wname = optimizer.get_workspace()
    name = optimizer.get_name()
    return {
        'username': username,
        'wname': wname,
        'name': name,
    }


@optimizers_bp.post('/')
@optimizers_bp.post('')
@token_auth.login_required
def create_optimizer(username, wname):
    return add_new_resource(username, wname, _DFL_OPTIM_NAME_)


@optimizers_bp.get('/<resource:name>/')
@optimizers_bp.get('/<resource:name>')
@token_auth.login_required
@linker.link_rule(_DFL_OPTIM_NAME_, blueprint=optimizers_bp)
def get_optimizer(username, wname, name):
    """
    :param username:
    :param wname:
    :param name:
    :return:
    """
    resource, response = get_resource(username, wname, _DFL_OPTIM_NAME_, name=name)
    if response is not None:    # error
        return response
    else:
        data = linker.make_links(resource.to_dict())
        return make_success_dict(HTTPStatus.OK, data=data)


@optimizers_bp.patch('/<resource:name>/')
@optimizers_bp.patch('/<resource:name>')
@token_auth.login_required
@check_json(True, optionals={'name', 'description', 'build'})
def update_optimizer(username, wname, name):
    """
    :param username:
    :param wname:
    :param name:
    :return:
    """
    data, opts, extras = get_check_json_data()
    return update_resource(username, wname, _DFL_OPTIM_NAME_, name, data)


@optimizers_bp.delete('/<resource:name>/')
@optimizers_bp.delete('/<resource:name>')
@token_auth.login_required
def delete_optimizer(username, wname, name):
    return delete_resource(username, wname, _DFL_OPTIM_NAME_, name)


__all__ = [
    'optimizers_bp',
    'create_optimizer',
    'get_optimizer',
    'update_optimizer',
    'delete_optimizer',
]