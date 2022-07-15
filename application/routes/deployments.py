from flask import Blueprint, request
from http import HTTPStatus

from application.utils import *
from .auth import token_auth
from .resources import *


_DFL_DEPLOYED_MODEL_NAME_ = "DeployedModel"


deployments_bp = Blueprint('deployments', __name__,
                           url_prefix='/users/<user:username>/workspaces/<workspace:wname>/deployments')


@linker.args_rule(_DFL_DEPLOYED_MODEL_NAME_)
def deployed_model_args(model):
    username = model.get_owner().get_name()
    wname = model.get_workspace().get_name()
    name = model.get_name()
    return {
        'username': username,
        'wname': wname,
        'name': name,
    }


@deployments_bp.post('/')
@deployments_bp.post('')
@token_auth.login_required
def create_deployed_model(username, wname):
    """
    Handles creation of a new DeployedModel resource for predictions.
    Request Syntax:
    {
        "name": ...,
        "description": ...,
        "path": ...,
        "deploy": ... # deployment config selection
    }
    :param username:
    :param wname:
    :return:
    """
    return add_new_resource(username, wname, _DFL_DEPLOYED_MODEL_NAME_, required={'name', 'path', 'deploy'})


@deployments_bp.get('/<resource:name>/')
@deployments_bp.get('/<resource:name>')
@token_auth.login_required
@linker.link_rule(_DFL_DEPLOYED_MODEL_NAME_, blueprint=deployments_bp)
def get_deployed_model(username, wname, name):
    """
    Returns description and metadata of a deployed model.
    :param username:
    :param wname:
    :param name:
    :return:
    """
    resource, response = get_resource(username, wname, _DFL_DEPLOYED_MODEL_NAME_, name=name)
    if response is not None:    # error
        return response
    else:
        data = linker.make_links(resource.to_dict())
        return make_success_dict(HTTPStatus.OK, data=data)


@deployments_bp.patch('/<resource:name>/metadata/')
@deployments_bp.patch('/<resource:name>/metadata')
@token_auth.login_required
@check_json(False, optionals={'name', 'description'})
def update_deployed_model_metadata(username, wname, name):
    """
    :param username:
    :param wname:
    :param name:
    :return:
    """
    data, opts, extras = get_check_json_data()
    return update_resource(username, wname, _DFL_DEPLOYED_MODEL_NAME_, name, data)


@deployments_bp.patch('/<resource:name>/redeploy/')
@deployments_bp.patch('/<resource:name>/redeploy')
@token_auth.login_required
@check_json(False, required={'name', 'path', 'deploy'}, optionals={'description'})
def redeploy_model(username, wname, name):
    """
    Redeploys a previously deployed model, i.e. substitutes the previous model
    and model metadata with a new one. Syntax is like 'create_deployed_model'.
    :param username:
    :param wname:
    :param name:
    :return:
    """
    data, opts, extras = get_check_json_data()
    return update_resource(username, wname, _DFL_DEPLOYED_MODEL_NAME_, name, data)


@deployments_bp.delete('/<resource:name>/')
@deployments_bp.delete('/<resource:name>')
@token_auth.login_required
def delete_deployed_model(username, wname, name):
    """
    :param username:
    :param wname:
    :param name:
    :return:
    """
    return delete_resource(username, wname, _DFL_DEPLOYED_MODEL_NAME_, name)


__all__ = [
    'deployments_bp',

    'create_deployed_model',
    'get_deployed_model',
    'update_deployed_model_metadata',

    'redeploy_model',
    'delete_deployed_model',
]