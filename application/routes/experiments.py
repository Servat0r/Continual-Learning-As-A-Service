from __future__ import annotations

import sys
import traceback
from flask import Blueprint, request, Response, send_file
from http import HTTPStatus

from application.errors import *
from application.utils import *
from application.database import *

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


# @executor.job
def _experiment_run_task(experiment_config: MongoCLExperimentConfig,
                         context: UserWorkspaceResourceContext) -> Response:
    context.stack = []
    response = None
    app = db.app
    with app.app_context():
        try:
            with experiment_config.resource_write():
                try:
                    experiment: BaseCLExperiment = experiment_config.build(context, locked=True)
                    if experiment is None:
                        response = make_error(HTTPStatus.INTERNAL_SERVER_ERROR, msg="Failed to initialize experiment!")
                    else:
                        start_result = experiment_config.set_started(locked=True)
                        if start_result is None:
                            response = make_error(
                                HTTPStatus.INTERNAL_SERVER_ERROR,
                                msg=f"Failed to start experiment #{start_result}.")
                        else:
                            result = experiment.run(
                                experiment_config.get_last_execution().base_dir(),
                            )
                            if result is None:
                                response = ResourceNotFound(msg="Experiment run configuration does not exist.")
                            elif result:
                                response = make_success_dict(msg=f"Experiment #{start_result} correctly executed.")
                            else:
                                response = make_error(
                                    HTTPStatus.INTERNAL_SERVER_ERROR,
                                    msg=f"Failed to run experiment #{start_result}.")
                    return response
                except Exception as ex:
                    exc_info = sys.exc_info()
                    traceback.print_exception(*exc_info)
                    response = make_error(
                        HTTPStatus.INTERNAL_SERVER_ERROR,
                        msg=f"Error when executing experiment #{start_result}: {ex.args[0]}.")
                    return response
                finally:
                    res, exc = experiment_config.set_finished(response=response, locked=True)
                    if not res:
                        response = make_error(
                            HTTPStatus.INTERNAL_SERVER_ERROR,
                            msg=f"Error when setting experiment #{start_result} status to 'ENDED': {exc.args[0]}.",
                        )
                        return response
        except Exception as ex:
            print(ex)


@experiments_bp.post('/')
@experiments_bp.post('')
@token_auth.login_required
def create_experiment(username, wname):
    return add_new_resource(username, wname, _DFL_EXPERIMENT_NAME)


@experiments_bp.patch('/<experiment:name>/setup/')
@experiments_bp.patch('/<experiment:name>/setup')
@token_auth.login_required
def setup_experiment(username, wname, name):

    experiment_config, err_response = get_resource(username, wname, _DFL_EXPERIMENT_NAME, name)
    if err_response is not None:
        return err_response

    result, ex = experiment_config.setup()
    if result:
        return make_success_dict(msg="Setup successfully completed.")
    else:
        return InternalFailure(msg=f"Setup failed: {ex}: '{ex.args[0]}'.")


@experiments_bp.patch('/<experiment:name>/')
@experiments_bp.patch('/<experiment:name>')
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


def __start_experiment(experiment_config: MongoCLExperimentConfig, context: UserWorkspaceResourceContext):
    uri = experiment_config.uri
    executor.submit_stored(uri, _experiment_run_task, experiment_config, context)
    # _experiment_run_task.submit_stored(uri, experiment_config, context)
    return make_success_dict(msg="Experiment successfully submitted!")


@experiments_bp.get('/<experiment:name>/status/')
@experiments_bp.get('/<experiment:name>/status')
@token_auth.login_required
def get_experiment_status(username, wname, name):
    experiment_config, err_response = get_resource(username, wname, _DFL_EXPERIMENT_NAME, name)
    if err_response:
        return err_response
    else:
        uri = experiment_config.uri
        if experiment_config.status != BaseCLExperiment.ENDED:
            return ResourceInUse(
                msg="Experiment is still running.",
                payload={'status': experiment_config.status},
            )
        elif not executor.futures.done(uri):
            # noinspection PyProtectedMember
            status = executor.futures._state(uri)
            print(status)
            return ResourceInUse(
                msg="Experiment has completed but its handler has not yet terminated.",
                payload={'status': status},
            )
        else:
            return make_success_dict(data={'status': experiment_config.status})


@experiments_bp.get('/<experiment:name>/results/exec/')
@experiments_bp.get('/<experiment:name>/results/exec')
@token_auth.login_required
def get_experiment_results(username, wname, name):
    experiment_config, err_response = get_resource(username, wname, _DFL_EXPERIMENT_NAME, name)
    exec_id = experiment_config.current_exec_id
    return get_experiment_execution_results(username, wname, name, exec_id)


@experiments_bp.get('/<experiment:name>/results/exec/<int:exec_id>/')
@experiments_bp.get('/<experiment:name>/results/exec/<int:exec_id>')
@token_auth.login_required
def get_experiment_execution_results(username, wname, name, exec_id):
    experiment_config, err_response = get_resource(username, wname, _DFL_EXPERIMENT_NAME, name)
    if err_response:
        return err_response
    elif exec_id <= len(experiment_config.executions):
        if exec_id == experiment_config.current_exec_id:
            uri = experiment_config.uri
            if experiment_config.status != BaseCLExperiment.ENDED:
                return ResourceInUse(msg="Experiment is still running and results are not available.")
            else:
                executor.futures.pop(uri)

        execution = experiment_config.get_execution(exec_id)
        data = execution.to_dict()
        return make_success_dict(
            msg="Results successfully retrieved.",
            data=data,
        )
    else:
        return ResourceNotFound(resource=f"execution<{exec_id}>")


@experiments_bp.get('/<experiment:name>/settings/')
@experiments_bp.get('/<experiment:name>/settings')
@token_auth.login_required
def get_experiment_settings(username, wname, name):
    experiment_config, err_response = get_resource(username, wname, _DFL_EXPERIMENT_NAME, name)
    if err_response:
        return err_response
    else:
        data = experiment_config.to_dict(settings=True)
        print(data)
        return make_success_dict(data=data)


@experiments_bp.get('/<experiment:name>/model/')
@experiments_bp.get('/<experiment:name>/model')
@token_auth.login_required
def get_experiment_model(username, wname, name):
    experiment_config, err_response = get_resource(username, wname, _DFL_EXPERIMENT_NAME, name)
    if err_response:
        return err_response
    else:
        exec_id = experiment_config.current_exec_id
        return get_experiment_execution_model(username, wname, name, exec_id)


@experiments_bp.get('/<experiment:name>/model/<int:exec_id>/')
@experiments_bp.get('/<experiment:name>/model/<int:exec_id>')
@token_auth.login_required
def get_experiment_execution_model(username, wname, name, exec_id):
    experiment_config, err_response = get_resource(username, wname, _DFL_EXPERIMENT_NAME, name)
    if err_response:
        return err_response
    else:
        execution = experiment_config.get_execution(exec_id)
        if execution.completed:
            try:
                model_fd = execution.get_final_model(descriptor=True)
                print(type(model_fd))
                return send_file(model_fd, attachment_filename='model.pt')
            except Exception as ex:
                return InternalFailure(msg=f"Error when sending model file: '{ex.args[0]}'.")
        else:
            return ResourceInUse(msg="Experiment is still running and results are not available.")


@experiments_bp.get('/<experiment:name>/results/csv/')
@experiments_bp.get('/<experiment:name>/results/csv')
@token_auth.login_required
def get_experiment_csv_results(username, wname, name):
    experiment_config, err_response = get_resource(username, wname, _DFL_EXPERIMENT_NAME, name)
    if err_response:
        return err_response
    else:
        exec_id = experiment_config.current_exec_id
        return get_experiment_execution_csv_results(username, wname, name, exec_id)


@experiments_bp.get('/<experiment:name>/results/csv/<int:exec_id>/')
@experiments_bp.get('/<experiment:name>/results/csv/<int:exec_id>')
@token_auth.login_required
def get_experiment_execution_csv_results(username, wname, name, exec_id):
    experiment_config, err_response = get_resource(username, wname, _DFL_EXPERIMENT_NAME, name)
    if err_response:
        return err_response
    else:
        execution = experiment_config.get_execution(exec_id)
        completed, results = execution.get_csv_results()
        if completed:
            if results is not None:
                return make_success_dict(data=results)
            else:
                return ResourceNotFound(msg="Experiment has completed but csv files are still not available.")
        else:
            return ResourceInUse(msg="Experiment is still running and csv results are not available.")


@experiments_bp.delete('/<experiment:name>/')
@experiments_bp.delete('/<experiment:name>')
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