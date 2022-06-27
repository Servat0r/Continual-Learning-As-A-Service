from __future__ import annotations

import io
import sys
import traceback
import json
from PIL import Image

import torch
from torchvision.transforms import ToTensor
from flask import Blueprint, request, Response, send_file
from http import HTTPStatus

from application.errors import *
from application.utils import *
from application.database import *

from application.resources.contexts import UserWorkspaceResourceContext
from application.resources.base import DataType, ReferrableDataType
from application.resources.datatypes import BaseCLExperiment

from application.mongo.resources.benchmarks import TransformConfig
from application.mongo.resources.experiments import MongoCLExperimentConfig

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


def get_transform(username, wname, info):
    transform_data = info.get('transform', None)
    if transform_data is not None:
        transform_config: t.Type[TransformConfig] = TransformConfig.get_by_name(transform_data)
        context = UserWorkspaceResourceContext(username, wname)
        transform: TransformConfig | None = transform_config.create(transform_data, context)
        return transform.get_transform()
    return ToTensor()


def transform_image(image_bytes, transform) -> torch.Tensor:
    image = Image.open(io.BytesIO(image_bytes))
    return transform(image).unsqueeze(0)


def predict(model, image_bytes, transform):
    tensor = transform_image(image_bytes, transform)
    device = get_device()
    tensor = tensor.to(device)
    model.eval()
    outputs = model.forward(tensor)
    _, y_hat = outputs.max(1)
    return y_hat.item()


@predictions_bp.get('/<experiment:name>/<int:exec_id>/')
@predictions_bp.get('/<experiment:name>/<int:exec_id>')
@token_auth.login_required
def get_prediction(username, wname, name, exec_id):
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
    experiment_config, err_response = get_resource(username, wname, _DFL_EXPERIMENT_NAME, name)
    if err_response:
        return err_response
    filestores = request.files
    if len(filestores) < 1:
        return make_error(HTTPStatus.BAD_REQUEST, "Missing file")   # todo replace with _MissingFile()
    info = json.load(filestores.getlist('info')[0].stream)
    transform = get_transform(username, wname, info)
    input_data = filestores.getlist('files')[0]
    execution = experiment_config.get_execution(exec_id)
    if execution.completed:
        try:
            model_fd = execution.get_final_model(descriptor=True)
            model = torch.load(model_fd).to(get_device())
            image_bytes = input_data.read()
            result = predict(model, image_bytes, transform)
            return make_success_dict(HTTPStatus.OK, msg="Prediction correctly executed", data={'class_id': result})
        except Exception as ex:
            return InternalFailure(msg=f"Error when sending model file: '{ex.args[0]}'.")
    else:
        return ResourceInUse(msg="Experiment is still running and results are not available.")


__all__ = [
    'predictions_bp',
    'get_prediction',
]