from flask import Blueprint, request
from http import HTTPStatus

from application.utils import checked_json, make_success_dict
from .auth import token_auth
from .resources import *


_DFL_METRICSET_NAME_ = "StandardMetricSet"


metricsets_bp = Blueprint('metricsets', __name__,
                          url_prefix='/users/<user:username>/workspaces/<workspace:wname>/metricsets')


@metricsets_bp.post('/')
@metricsets_bp.post('')
@token_auth.login_required
def create_metric_set(username, wname):
    return add_new_resource(username, wname, _DFL_METRICSET_NAME_)


@metricsets_bp.get('/<resource:name>/')
@metricsets_bp.get('/<resource:name>')
@token_auth.login_required
def get_metricset(username, wname, name):
    """
    :param username: 
    :param wname: 
    :param name: 
    :return: 
    """
    resource, response = get_resource(username, wname, _DFL_METRICSET_NAME_, name)
    if response is not None:    # error
        return response
    else:
        return make_success_dict(HTTPStatus.OK, resource.to_dict())


@metricsets_bp.patch('/<resource:name>/')
@metricsets_bp.patch('/<resource:name>')
@token_auth.login_required
def update_metricset(username, wname, name):
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
        return update_resource(username, wname, _DFL_METRICSET_NAME_, name, data)


@metricsets_bp.delete('/<resource:name>/')
@metricsets_bp.delete('/<resource:name>')
@token_auth.login_required
def delete_metric_set(username, wname, name):
    """
    :param username:
    :param wname:
    :param name:
    :return:
    """
    return delete_resource(username, wname, _DFL_METRICSET_NAME_, name)


__all__ = [
    'metricsets_bp',
    'create_metric_set',
    'get_metricset',
    'update_metricset',
    'delete_metric_set',
]