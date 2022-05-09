from flask import Blueprint, request

from application.utils import checked_json
from .auth import token_auth
from .resources import *


_DFL_OPTIM_NAME_ = "CLOptimizer"


optimizers_bp = Blueprint('optimizers', __name__,
                          url_prefix='/users/<user:username>/workspaces/<workspace:wname>/optimizers')


@optimizers_bp.post('/')
@optimizers_bp.post('')
@token_auth.login_required
def create_optimizer(username, wname):
    return add_new_resource(username, wname, _DFL_OPTIM_NAME_)


@optimizers_bp.get('/<name>/')
@optimizers_bp.get('/<name>')
@token_auth.login_required
def build_optimizer(username, wname, name):
    return build_resource(username, wname, _DFL_OPTIM_NAME_, name)


@optimizers_bp.patch('/<name>/')
@optimizers_bp.patch('/<name>/')
@token_auth.login_required
def update_optimizer(username, wname, name):
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
        return update_resource(username, wname, _DFL_OPTIM_NAME_, name, data)


@optimizers_bp.delete('/<name>/')
@optimizers_bp.delete('/<name>')
@token_auth.login_required
def delete_optimizer(username, wname, name):
    return delete_resource(username, wname, _DFL_OPTIM_NAME_, name)


__all__ = [
    'optimizers_bp',
    'create_optimizer',
    'build_optimizer',
    'update_optimizer',
    'delete_optimizer',
]