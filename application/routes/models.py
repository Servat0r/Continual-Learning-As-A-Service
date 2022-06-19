from flask import Blueprint, request

from application.utils import checked_json
from .auth import token_auth
from .resources import *


_DFL_MODEL_NAME_ = "Model"


models_bp = Blueprint('models', __name__,
                      url_prefix='/users/<user:username>/workspaces/<workspace:wname>/models')


@models_bp.post('/')
@models_bp.post('')
@token_auth.login_required
def create_model(username, wname):
    return add_new_resource(username, wname, _DFL_MODEL_NAME_)


@models_bp.get('/<resource:name>/')
@models_bp.get('/<resource:name>')
def get_model(username, wname, name):
    """
    :param username: 
    :param wname: 
    :param name: 
    :return: 
    """
    return get_resource(username, wname, _DFL_MODEL_NAME_, name)


@models_bp.patch('/<resource:name>/')
@models_bp.patch('/<resource:name>/')
@token_auth.login_required
def update_model(username, wname, name):
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
        return update_resource(username, wname, _DFL_MODEL_NAME_, name, data)


@models_bp.delete('/<resource:name>/')
@models_bp.delete('/<resource:name>')
@token_auth.login_required
def delete_model(username, wname, name):
    return delete_resource(username, wname, _DFL_MODEL_NAME_, name)


__all__ = [
    'models_bp',
    'create_model',
    'get_model',
    'update_model',
    'delete_model',
]