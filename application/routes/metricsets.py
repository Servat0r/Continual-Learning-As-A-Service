from flask import Blueprint
from http import HTTPStatus

from application.utils import *
from .auth import token_auth
from .resources import *


_DFL_METRICSET_NAME_ = "StandardMetricSet"


metricsets_bp = Blueprint('metricsets', __name__,
                          url_prefix='/users/<user:username>/workspaces/<workspace:wname>/metricsets')


@linker.args_rule(_DFL_METRICSET_NAME_)
def metricset_args(metricset):
    username = metricset.get_owner().get_name()
    wname = metricset.get_workspace()
    name = metricset.get_name()
    return {
        'username': username,
        'wname': wname,
        'name': name,
    }


@metricsets_bp.post('/')
@metricsets_bp.post('')
@token_auth.login_required
def create_metric_set(username, wname):
    return add_new_resource(username, wname, _DFL_METRICSET_NAME_)


@metricsets_bp.get('/<resource:name>/')
@metricsets_bp.get('/<resource:name>')
@token_auth.login_required
@linker.link_rule(_DFL_METRICSET_NAME_, blueprint=metricsets_bp)
def get_metricset(username, wname, name):
    """
    :param username:
    :param wname:
    :param name:
    :return:
    """
    resource, response = get_resource(username, wname, _DFL_METRICSET_NAME_, name=name)
    if response is not None:    # error
        return response
    else:
        data = linker.make_links(resource.to_dict())
        return make_success_dict(HTTPStatus.OK, data=data)


@metricsets_bp.patch('/<resource:name>/')
@metricsets_bp.patch('/<resource:name>')
@token_auth.login_required
@check_json(False, optionals={'name', 'description', 'build'})
def update_metricset(username, wname, name):
    """
    :param username:
    :param wname:
    :param name:
    :return:
    """
    data, opts, extras = get_check_json_data()
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