"""
Common constants.
"""
from __future__ import annotations
from typing import Any
from http import HTTPStatus

import torch
from flask import Request, Response, jsonify
from werkzeug.exceptions import BadRequest
from .errors import *

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
                 force: bool = True) -> tuple[Any | None, ServerResponseError | None, list[str], list[str]]:
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


def get_device():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


__all__ = [
    'GET', 'PUT', 'POST', 'PATCH',
    'OPTIONS', 'HEAD', 'DELETE',
    'make_success_kwargs',
    'make_success_dict',
    'checked_json',
    'get_device',
]