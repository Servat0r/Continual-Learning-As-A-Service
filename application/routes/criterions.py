from flask import Blueprint, request
from http import HTTPStatus

from application.utils import checked_json, make_success_dict, linker
from .auth import token_auth
from .resources import *


_DFL_CRITERION_NAME = "CLCriterion"


criterions_bp = Blueprint('criterions', __name__,
                          url_prefix='/users/<user:username>/workspaces/<workspace:wname>/criterions')


@linker.args_rule('CLCriterion')
def criterion_args(criterion):
    username = criterion.get_owner().get_name()
    wname = criterion.get_workspace()
    name = criterion.get_name()
    return {
        'username': username,
        'wname': wname,
        'name': name,
    }


@criterions_bp.post('/')
@criterions_bp.post('')
@token_auth.login_required
def create_criterion(username, wname):
    return add_new_resource(username, wname, _DFL_CRITERION_NAME)


@criterions_bp.get('/<resource:name>/')
@criterions_bp.get('/<resource:name>')
@token_auth.login_required
@linker.link_rule('CLCriterion', blueprint=criterions_bp)
def get_criterion(username, wname, name):
    """
    :param username:
    :param wname:
    :param name:
    :return:
    """
    resource, response = get_resource(username, wname, _DFL_CRITERION_NAME, name=name)
    if response is not None:    # error
        return response
    else:
        data = linker.make_links(resource.to_dict())
        return make_success_dict(HTTPStatus.OK, data=data)


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
    'get_criterion',
    'update_criterion',
    'delete_criterion',
]