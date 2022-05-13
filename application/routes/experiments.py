from flask import Blueprint, request, Response
from http import HTTPStatus

from application.errors import *
from application.utils import *

from application.resources.contexts import UserWorkspaceResourceContext
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


# todo spostare!
@executor.job
def _experiment_run_task(experiment_config: MongoCLExperimentConfig,
                         context: UserWorkspaceResourceContext) -> Response:

    with experiment_config.resource_write():
        try:
            experiment: BaseCLExperiment = experiment_config.build(context, locked=True)
            if experiment is None:
                return make_error(HTTPStatus.INTERNAL_SERVER_ERROR, msg="Failed to initialize experiment!")

            result = experiment_config.set_started(locked=True)
            if not result:
                return make_error(HTTPStatus.INTERNAL_SERVER_ERROR, msg="Failed to start experiment.")

            result = experiment.run()

            if result is None:
                return ResourceNotFound(msg="Experiment run configuration does not exist.")
            elif result:
                return make_success_dict(msg="Experiment correctly executed.")
            else:
                return make_error(HTTPStatus.INTERNAL_SERVER_ERROR, msg="Failed to run experiment.")
        except Exception as ex:
            return make_error(HTTPStatus.INTERNAL_SERVER_ERROR, msg=f"Error when executing experiment: {ex.args[0]}.")
        finally:
            experiment_config.set_finished(locked=True)


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
        return make_success_dict(msg="Setup successfully completed.")
    else:
        return make_error(HTTPStatus.INTERNAL_SERVER_ERROR, msg="Setup failed.")  # todo che errore?


@experiments_bp.patch('/<name>/')
@experiments_bp.patch('/<name>')
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
            context = UserWorkspaceResourceContext(username, wname)
            return __start_experiment(experiment_config, context)
        elif status == _EXPERIMENT_STOP:
            return RouteNotImplemented()


# TODO Capire come eseguire i controlli di _experiment_run_task PRIMA di rispondere!
def __start_experiment(experiment_config: MongoCLExperimentConfig, context: UserWorkspaceResourceContext):
    uri = experiment_config.uri
    _experiment_run_task.submit_stored(uri, experiment_config, context)
    return make_success_dict(msg="Experiment successfully started!")


@experiments_bp.get('/<name>/status/')
@experiments_bp.get('/<name>/status')
@token_auth.login_required
def get_experiment_status(username, wname, name):
    experiment_config, err_response = get_resource(username, wname, _DFL_EXPERIMENT_NAME, name)
    if err_response:
        return err_response
    else:
        uri = experiment_config.uri
        if experiment_config.status != BaseCLExperiment.ENDED:
            return make_success_dict(
                HTTPStatus.LOCKED,
                data={'status': experiment_config.status},
            )
        elif not executor.futures.done(uri):
            # noinspection PyProtectedMember
            status = executor.futures._state(uri)
            print(status)
            return make_success_dict(
                HTTPStatus.LOCKED,
                data={'status': status},
            )
        else:
            return make_success_dict(data={'status': experiment_config.status})


@experiments_bp.get('/<name>/results/')
@experiments_bp.get('/<name>/results')
@token_auth.login_required
def get_experiment_results(username, wname, name):
    experiment_config, err_response = get_resource(username, wname, _DFL_EXPERIMENT_NAME, name)
    if err_response:
        return err_response
    else:
        uri = experiment_config.uri
        if experiment_config.status != BaseCLExperiment.ENDED:
            return make_success_dict(
                HTTPStatus.LOCKED,
                msg="Experiment is still running and results are not available.",
            )
        else:
            future = executor.futures.pop(uri)
            if future is not None:
                result = future.result()
                if result is not None:
                    return result
            return make_success_dict(
                HTTPStatus.NOT_FOUND,
                msg="No results available for this experiment.",
            )


@experiments_bp.get('/<name>/settings/')
@experiments_bp.get('/<name>/settings')
@token_auth.login_required
def get_experiment_settings(username, wname, name):
    experiment_config, err_response = get_resource(username, wname, _DFL_EXPERIMENT_NAME, name)
    if err_response:
        return err_response
    else:
        data = experiment_config.to_dict()
        print(data)
        return make_success_dict(data=data)


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
    'get_experiment_results',
    'get_experiment_settings',
    'get_experiment_model',
    'get_experiment_csv_results',
    'delete_experiment',
]