from flask import Blueprint

from application.routes.auth import token_auth
from application.routes.resources import *


_DFL_BENCHMARK_NAME_ = "Benchmark"


benchmarks_bp = Blueprint('benchmarks', __name__,
                          url_prefix='/users/<user:username>/workspaces/<workspace:wname>/benchmarks')


@benchmarks_bp.post('/')
@benchmarks_bp.post('')
@token_auth.login_required
def create_benchmark(username, wname):
    return add_new_resource(username, wname, _DFL_BENCHMARK_NAME_)


@benchmarks_bp.get('/<name>/')
@benchmarks_bp.get('/<name>')
@token_auth.login_required
def build_benchmark(username, wname, name):
    """
    :param username:
    :param wname:
    :param name:
    :return:
    """
    return build_resource(username, wname, _DFL_BENCHMARK_NAME_, name)


@benchmarks_bp.delete('/<name>/')
@benchmarks_bp.delete('/<name>')
@token_auth.login_required
def delete_benchmark(username, wname, name):
    """
    :param username:
    :param wname:
    :param name:
    :return:
    """
    return delete_resource(username, wname, _DFL_BENCHMARK_NAME_, name)