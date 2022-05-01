from flask import Blueprint

from application.routes.auth import token_auth
from application.routes.resources import *


_DFL_METRICSET_NAME_ = "StandardMetricSet"


metricsets_bp = Blueprint('metricsets', __name__,
                          url_prefix='/users/<user:username>/workspaces/<workspace:wname>/metricsets')


@metricsets_bp.post('/')
@metricsets_bp.post('')
@token_auth.login_required
def create_metric_set(username, wname):
    return add_new_resource(username, wname, _DFL_METRICSET_NAME_)


@metricsets_bp.get('/<name>/')
@metricsets_bp.get('/<name>')
@token_auth.login_required
def build_metric_set(username, wname, name):
    """
    :param username:
    :param wname:
    :param name:
    :return:
    """
    return build_resource(username, wname, _DFL_METRICSET_NAME_, name)


@metricsets_bp.patch('/<name>/')
@metricsets_bp.patch('/<name>/')
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


@metricsets_bp.delete('/<name>/')
@metricsets_bp.delete('/<name>')
@token_auth.login_required
def delete_metric_set(username, wname, name):
    """
    :param username:
    :param wname:
    :param name:
    :return:
    """
    return delete_resource(username, wname, _DFL_METRICSET_NAME_, name)