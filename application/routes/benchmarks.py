from flask import Blueprint
from http import HTTPStatus

from application.utils import *

from .auth import token_auth
from .resources import *


_DFL_BENCHMARK_NAME_ = "Benchmark"


benchmarks_bp = Blueprint('benchmarks', __name__,
                          url_prefix='/users/<user:username>/workspaces/<workspace:wname>/benchmarks')


@linker.args_rule('Benchmark')
def benchmark_args(benchmark):
    username = benchmark.get_owner().get_name()
    wname = benchmark.get_workspace()
    name = benchmark.get_name()
    return {
        'username': username,
        'wname': wname,
        'name': name,
    }


@benchmarks_bp.post('/')
@benchmarks_bp.post('')
@token_auth.login_required
def create_benchmark(username, wname):
    return add_new_resource(username, wname, typename=_DFL_BENCHMARK_NAME_)


@benchmarks_bp.get('/<resource:name>/')
@benchmarks_bp.get('/<resource:name>')
@token_auth.login_required
@linker.link_rule('Benchmark', blueprint=benchmarks_bp)
def get_benchmark(username, wname, name):
    """
    :param username:
    :param wname:
    :param name:
    :return:
    """
    resource, response = get_resource(username, wname, typename=_DFL_BENCHMARK_NAME_, name=name)
    if response is not None:    # error
        return response
    else:
        data = linker.make_links(resource.to_dict())
        return make_success_dict(HTTPStatus.OK, data=data)


@benchmarks_bp.patch('/<resource:name>/')
@benchmarks_bp.patch('/<resource:name>')
@token_auth.login_required
@check_json(False, optionals={'name', 'description', 'build'})
def update_benchmark(username, wname, name):
    """
    :param username:
    :param wname:
    :param name:
    :return:
    """
    data, opts, extras = get_check_json_data()
    return update_resource(username, wname, typename=_DFL_BENCHMARK_NAME_, name=name, updata=data)


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
    return delete_resource(username, wname, typename=_DFL_BENCHMARK_NAME_, name=name)


__all__ = [
    'benchmarks_bp',
    'create_benchmark',
    'get_benchmark',
    'update_benchmark',
    'delete_benchmark',
]