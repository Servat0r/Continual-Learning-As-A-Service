from __future__ import annotations

import io
import json
from werkzeug.datastructures import FileStorage

import torch
from torchvision.transforms import ToTensor
from flask import Blueprint, request
from http import HTTPStatus

from application.errors import *
from application.utils import *

from application.resources.contexts import UserWorkspaceResourceContext
from application.resources.base import DataType, ReferrableDataType
from application.resources.datatypes import BaseCLExperiment

from application.mongo.resources.benchmarks import TransformConfig

from .auth import token_auth
from .resources import *

predictions_bp = Blueprint(
    'predictions', __name__,
    url_prefix='/users/<user:username>/workspaces/<workspace:wname>/predictions',
)

_DFL_EXPERIMENT_NAME = t.cast(
    t.Type[ReferrableDataType],
    DataType.get_type(BaseCLExperiment.canonical_typename()),
)

_DFL_DEPLOYED_MODEL_NAME_ = "DeployedModel"



def get_transform(username, wname, info):
    transform_data = info.get('transform', None)
    if transform_data is not None:
        transform_config: t.Type[TransformConfig] = TransformConfig.get_by_name(transform_data)
        context = UserWorkspaceResourceContext(username, wname)
        transform: TransformConfig | None = transform_config.create(transform_data, context)
        return transform.get_transform()
    return ToTensor()


def predict(model: Module, input_data: list[FileStorage], transform, mode: str = 'plain') -> dict[str, int] | NotImplemented:
    if mode == 'plain':
        input_bytes: dict[str, io.BytesIO] = {inp.filename: inp.read() for inp in input_data}
        output_bytes: dict[str, int] = {}
        # input_bytes = [inp.read() for inp in input_data]
        tensors = [transform(item_bytes).unsqueeze(0) for item_bytes in input_bytes.values()]
        device = get_device()
        tensors = [tensor.to(device) for tensor in tensors]
        batch_tensor = torch.stack(tensors)
        batch_tensor = batch_tensor.to(device)
        model.eval()
        outputs: torch.Tensor = model(batch_tensor)
        _, y_hat = outputs.max(1)
        y_hat = y_hat.to('cpu').numpy().astype(int)
        i = 0
        for filename in input_bytes.keys():
            output_bytes[filename] = int(y_hat[i])
            i += 1
        return output_bytes
    elif mode == 'zip':
        return NotImplemented
    else:
        raise ValueError(f"Unknown file transfer mode '{mode}'")


@predictions_bp.get('/experiments/<experiment:name>/')
@predictions_bp.get('/experiments/<experiment:name>')
@token_auth.login_required
def get_experiment_predictions(username, wname, name):
    """
    Shortcut for get_experiment_execution_predictions(...).
    :param username:
    :param wname:
    :param name:
    :return:
    """
    experiment_config, err_response = get_resource(username, wname, typename=_DFL_EXPERIMENT_NAME, name=name)
    if err_response:
        return err_response
    else:
        exec_id = experiment_config.current_exec_id
        return get_experiment_execution_predictions(username, wname, name, exec_id)


@predictions_bp.get('/experiments/<experiment:name>/<int:exec_id>/')
@predictions_bp.get('/experiments/<experiment:name>/<int:exec_id>')
@token_auth.login_required
def get_experiment_execution_predictions(username, wname, name, exec_id):
    """
    Request Syntax:
    {
        "transform": <input_transform>
    }
    + raw data
    :param username:
    :param wname:
    :param name:
    :param exec_id:
    :return:
    """
    experiment_config, err_response = get_resource(username, wname, typename=_DFL_EXPERIMENT_NAME, name=name)
    if err_response:
        return err_response
    filestores = request.files
    if len(filestores) < 1:
        return MissingFile()
    info = json.load(filestores.getlist('info')[0].stream)
    transform = get_transform(username, wname, info)
    mode = info.get('mode', 'plain')    # file transfer mode (similar to that for data repositories)
    input_data = filestores.getlist('files')
    execution = experiment_config.get_execution(exec_id)
    if execution.completed:
        try:
            model_fd = execution.get_final_model(descriptor=True)
            model = torch.load(model_fd).to(get_device())
            result = predict(model, input_data, transform, mode=mode)
            if result == NotImplemented:
                return RouteNotImplemented(HTTPStatus.NOT_IMPLEMENTED, msg=f"'{mode}' file transfer is not implemented")
            else:
                return make_success_dict(HTTPStatus.OK, msg="Prediction correctly executed", data={'class_ids': result})
        except Exception as ex:
            return InternalFailure(msg=f"Error when sending model file: '{ex.args[0]}'.")
    else:
        return ResourceInUse(msg="Experiment is still running and results are not available.")


@predictions_bp.get('/deployments/<path:path>/')
@predictions_bp.get('/deployments/<path:path>')
@token_auth.login_required
def get_deployed_model_predictions(username, wname, path):
    path_list = path.split('/')
    path_list = [s for s in path_list if len(s) > 0]
    path = '/'.join(path_list)
    deployed_model_config, err_response = get_resource(username, wname, typename=_DFL_DEPLOYED_MODEL_NAME_, path=path)
    if err_response:
        return err_response
    filestores = request.files
    if len(filestores) < 1:
        return MissingFile()
    info = json.load(filestores.getlist('info')[0].stream)
    transform = get_transform(username, wname, info)
    mode = info.get('mode', 'plain')    # file transfer mode (similar to that for data repositories)
    input_data = filestores.getlist('files')
    context = UserWorkspaceResourceContext(username, wname)
    deployed_model = deployed_model_config.build(context)
    result = deployed_model.get_prediction(input_data, transform, mode)
    if result == NotImplemented:
        return RouteNotImplemented(HTTPStatus.NOT_IMPLEMENTED, msg=f"'{mode}' file transfer is not implemented")
    else:
        return make_success_dict(HTTPStatus.OK, msg="Prediction correctly executed", data={'class_ids': result})


__all__ = [
    'predictions_bp',

    'get_experiment_predictions',
    'get_experiment_execution_predictions',
    'get_deployed_model_predictions',
]