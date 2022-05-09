from flask import Blueprint, request
from http import HTTPStatus

from application.errors import *
from application.utils import checked_json, make_success_dict, make_success_kwargs, make_error, t

from application.resources.base import DataType, ReferrableDataType
from application.resources.datatypes import BaseCLExperiment

from application.mongo.resources.experiments import MongoCLExperimentConfig

from .auth import token_auth
from .resources import *

_DFL_EXPERIMENT_NAME = t.cast(
    t.Type[ReferrableDataType],
    DataType.get_type(BaseCLExperiment.canonical_typename()),
)

_EXPERIMENT_START = "START"
_EXPERIMENT_STOP = "STOP"

experiments_bp = Blueprint('experiments', __name__,
                           url_prefix='/users/<user:username>/workspaces/<workspace:wname>/experiments')


@experiments_bp.post('/')
@experiments_bp.post('')
@token_auth.login_required
def create_experiment(username, wname):
    return add_new_resource(username, wname, _DFL_EXPERIMENT_NAME)


@experiments_bp.patch('/<name>/setup/')
@experiments_bp.patch('/<name>/setup')
@token_auth.login_required
def setup_experiment(username, wname, name):

    experiment_config, err_response = get_resource(username, wname, _DFL_EXPERIMENT_NAME, name)
    if err_response is not None:
        return err_response

    result = experiment_config.setup()
    if result:
        return make_success_kwargs(msg="Setup successfully completed.")
    else:
        return make_error(HTTPStatus.INTERNAL_SERVER_ERROR, msg="Setup failed.")  # todo che errore?


@experiments_bp.patch('/<name>/status/')
@experiments_bp.patch('/<name>/status')
@token_auth.login_required
def set_experiment_status(username, wname, name):
    """
    RequestSyntax:
    {
        "status": "START"/"STOP"
    }
    :param username:
    :param wname:
    :param name:
    :return:
    """
    data, error, opts, extras = checked_json(request, False, {'status'})
    if error:
        if data:
            return error(**data)
        else:
            return error()
    else:
        experiment_config, err_response = get_resource(username, wname, _DFL_EXPERIMENT_NAME, name)
        if err_response:
            return err_response

        status = data['status']
        if status != _EXPERIMENT_START and status != _EXPERIMENT_STOP:
            return ForbiddenOperation(msg="You can only start or stop an experiment!")
        elif status == _EXPERIMENT_START:
            return __start_experiment(experiment_config)
        elif status == _EXPERIMENT_STOP:
            return __stop_experiment(experiment_config)


def __start_experiment(experiment_config: MongoCLExperimentConfig):
    result = experiment_config.set_started()
    if result:
        return make_success_kwargs(msg="Experiment successfully started!")
    else:
        return make_error(HTTPStatus.INTERNAL_SERVER_ERROR)


def __stop_experiment(experiment_config: MongoCLExperimentConfig):
    result = experiment_config.set_finished()
    if result:
        return make_success_kwargs(msg="Experiment successfully stopped!")
    else:
        return make_error(HTTPStatus.INTERNAL_SERVER_ERROR)


@experiments_bp.get('/<name>/status/')
@experiments_bp.get('/<name>/status')
@token_auth.login_required
def get_experiment_status(username, wname, name):
    experiment_config, err_response = get_resource(username, wname, _DFL_EXPERIMENT_NAME, name)
    if err_response:
        return err_response
    else:
        return make_success_kwargs(status=experiment_config.status)


@experiments_bp.get('/<name>/settings/')
@experiments_bp.get('/<name>/settings')
@token_auth.login_required
def get_experiment_settings(username, wname, name):
    experiment_config, err_response = get_resource(username, wname, _DFL_EXPERIMENT_NAME, name)
    if err_response:
        return err_response
    else:
        return make_success_dict(data=experiment_config.to_dict())


@experiments_bp.get('/<name>/model/')
@experiments_bp.get('/<name>/model')
@token_auth.login_required
def get_experiment_model(username, wname, name):
    return RouteNotImplemented()


@experiments_bp.get('/<name>/results/csv/')
@experiments_bp.get('/<name>/results/csv')
@token_auth.login_required
def get_experiment_csv_results(username, wname, name):
    return RouteNotImplemented()


@experiments_bp.delete('/<name>/')
@experiments_bp.delete('/<name>')
@token_auth.login_required
def delete_experiment(username, wname, name):
    return delete_resource(username, wname, _DFL_EXPERIMENT_NAME, name)


__all__ = [
    'experiments_bp',
    'create_experiment',
    'setup_experiment',
    'set_experiment_status',
    'get_experiment_status',
    'get_experiment_settings',
    'get_experiment_model',
    'get_experiment_csv_results',
    'delete_experiment',
]