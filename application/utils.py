"""
Common constants.
"""
from __future__ import annotations

import sys
import traceback
import typing as t
import os
from abc import ABC, abstractmethod
from datetime import datetime
from functools import wraps

import torch
from torch.nn.modules import Module
from http import HTTPStatus
from flask import Request, jsonify, Response
from werkzeug.exceptions import BadRequest
from flask_executor import Executor

from .errors import *

# Executor
executor = Executor()

# TypeVars
TBoolStr = t.TypeVar('TBoolStr', bound=tuple[bool, t.Optional[str]])
TBoolExc = t.TypeVar('TBoolExc', bound=tuple[bool, t.Optional[Exception]])
TBoolAny = t.TypeVar('TBoolAny', bound=tuple[bool, t.Any])
TOptBoolAny = t.TypeVar('TOptBoolAny', bound=tuple[t.Optional[bool], t.Any])
TDesc = t.TypeVar('TDesc', bound=dict[str, t.Any])

# Classic methods
GET = 'GET'
POST = 'POST'
PUT = 'PUT'
PATCH = 'PATCH'
HEAD = 'HEAD'
OPTIONS = 'OPTIONS'
DELETE = 'DELETE'

# Default success and error messages
_DFL_SUCCESS_MSG = 'Request successfully completed.'


def make_success_kwargs(status: int = HTTPStatus.OK, msg: str = _DFL_SUCCESS_MSG, **kwargs) -> Response:
    """
    Default success responses maker.
    :param status: HTTP success status code.
    :param msg: Descriptive message.
    :param kwargs: Extra arguments.
    :return: A Response object.
    """
    err_dict = kwargs if kwargs is not None else {}
    err_dict['message'] = msg

    response = jsonify(err_dict)
    response.status = status
    return response


def make_success_dict(status: int = HTTPStatus.OK, msg: str = _DFL_SUCCESS_MSG, data: dict = None) -> Response:
    if data is None:
        data = {}
    data['message'] = msg

    response = jsonify(data)
    response.status = status
    return response


def checked_json(request: Request, keyargs: bool = False, required: set[str] = None, optionals: set[str] = None,
                 force: bool = True) -> tuple[t.Any | None, ServerResponseError | None, list[str], list[str]]:
    """
    Checks if request data is JSON-syntactically correct and has exactly the expected parameters (even optional ones).
    :param request: Current incoming request.
    :param keyargs: If true, enables optional parameters in the request.
    :param required: Required parameters for this request.
    :param optionals: Optional parameters for this request (except for "key" extra arguments).
    :param force: To be passed to request.get_json(...).
    :return: A couple (dict, error), where error is None on success and an error as defined in
    application.errors.handlers on error, and dict is a dictionary that must be interpreted as:
        - on success, request body as JSON;
        - if error is BadJSONSyntax, an empty dictionary to be ignored;
        - if error is MissingParameter, a list of all missing required parameters;
        - if error is InvalidParameter, a list of all unexpected parameters.
    """
    if required is None:
        required = set()

    if optionals is None:
        optionals = set()

    if not required.isdisjoint(optionals):
        raise ValueError("'required' and 'optionals' sets must be disjoint!")

    try:
        data = request.get_json(force=force)
        if data is None:
            return None, BadJSONSyntax, [], []
        else:
            keys = data.keys()
            missing_params = required.copy()
            given_optionals: list[str] = []
            extras: list[str] = []
            opts_bak = optionals.copy()    # (deep copy in this case)

            for param in keys:
                if param in missing_params:
                    missing_params.remove(param)
                elif param in opts_bak:
                    opts_bak.remove(param)
                    given_optionals.append(param)
                else:
                    extras.append(param)

            if len(missing_params) > 0:
                return {'parameter': missing_params}, MissingParameter, given_optionals, extras
            elif (not keyargs) and (len(extras) > 0):
                return {'parameter': extras}, InvalidParameter, given_optionals, extras
            else:
                return data, None, given_optionals, extras
    except BadRequest:
        return None, BadJSONSyntax, [], []


# utility for PyTorch device selection
def get_device():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


# utility for common datasets
def get_all_common_datasets_root(abspath: bool = False) -> str:
    basepath = os.path.join('..', 'common', 'datasets')
    return os.path.abspath(basepath) if abspath else os.path.relpath(basepath, os.getcwd())


def get_common_dataset_root(dataset_name: str, abspath: bool = False) -> str:
    basepath = os.path.join(get_all_common_datasets_root(abspath), dataset_name)
    return os.path.abspath(basepath) if abspath else os.path.relpath(basepath, os.getcwd())


# Exception catcher
def catcher(exc_type: t.Type[Exception] = Exception, dfl_return: t.Any = None):
    def wrapper(f: t.Callable):
        @wraps(f)
        def new_f(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except exc_type as ex:
                traceback.print_exc(sys.exc_info())
                return dfl_return
        return new_f
    return wrapper


# The following function is copied from an older version of the `Continual Learning Baselines` project.
# Current project GitHub page is: https://github.com/ContinualAI/continual-learning-baselines.
# Original function comments and citations are left unchanged.
def get_average_metric(metric_dict: dict, metric_name: str = 'Top1_Acc_Stream'):
    """
    Compute the average of a metric based on the provided metric name.
    The average is computed across the instance of the metrics containing the
    given metric name in the input dictionary.
    :param metric_dict: dictionary containing metric name as keys and metric value as value.
        This dictionary is usually returned by the `eval` method of Avalanche strategies.
    :param metric_name: the metric name (or a part of it), to be used as pattern to filter the dictionary
    :return: a number representing the average of all the metric containing `metric_name` in their name
    """

    avg_stream_acc = []
    for k, v in metric_dict.items():
        if k.startswith(metric_name):
            avg_stream_acc.append(v)
    return sum(avg_stream_acc) / float(len(avg_stream_acc))


__all__ = [
    'executor',

    'TBoolStr', 'TBoolExc', 'TDesc',
    'TBoolAny', 'TOptBoolAny',

    'os', 'abstractmethod', 'ABC',
    'datetime', 't', 'catcher',

    'GET', 'PUT', 'POST', 'PATCH',
    'OPTIONS', 'HEAD', 'DELETE',

    'make_success_kwargs',
    'make_success_dict',
    'checked_json',

    'get_device',
    'Module',

    'get_all_common_datasets_root',
    'get_common_dataset_root',

    'get_average_metric',
]