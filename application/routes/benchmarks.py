from flask import Blueprint, request
from http import HTTPStatus

from application.utils import checked_json, make_success_dict
from .auth import token_auth
from .resources import *


_DFL_BENCHMARK_NAME_ = "Benchmark"


benchmarks_bp = Blueprint('benchmarks', __name__,
                          url_prefix='/users/<user:username>/workspaces/<workspace:wname>/benchmarks')


@benchmarks_bp.post('/')
@benchmarks_bp.post('')
@token_auth.login_required
def create_benchmark(username, wname):
    return add_new_resource(username, wname, _DFL_BENCHMARK_NAME_)


@benchmarks_bp.get('/<resource:name>/')
@benchmarks_bp.get('/<resource:name>')
@token_auth.login_required
def get_benchmark(username, wname, name):
    """
    :param username:
    :param wname:
    :param name:
    :return:
    """
    resource, response = get_resource(username, wname, _DFL_BENCHMARK_NAME_, name)
    if response is not None:    # error
        return response
    else:
        return make_success_dict(HTTPStatus.OK, resource.to_dict())


@benchmarks_bp.patch('/<resource:name>/')
@benchmarks_bp.patch('/<resource:name>')
@token_auth.login_required
def update_benchmark(username, wname, name):
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
        return update_resource(username, wname, _DFL_BENCHMARK_NAME_, name, data)


@benchmarks_bp.delete('/<resource:name>/')
@benchmarks_bp.delete('/<resource:name>')
@token_auth.login_required
def delete_benchmark(username, wname, name):
    """
    :param username:
    :param wname:
    :param name:
    :return:
    """
    return delete_resource(username, wname, _DFL_BENCHMARK_NAME_, name)


__all__ = [
    'benchmarks_bp',
    'create_benchmark',
    'get_benchmark',
    'update_benchmark',
    'delete_benchmark',
]