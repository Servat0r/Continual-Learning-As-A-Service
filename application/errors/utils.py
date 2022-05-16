from __future__ import annotations
from flask import Response, jsonify

_DFL_ERROR_MSG = 'An error occurred. See status code for more information.'


def make_error(
        status: int, msg: str = _DFL_ERROR_MSG, err_type: str | None = None,
        payload: dict = None, **kwargs) -> Response:
    """
    Default error responses maker.
    :param status: HTTP error status code.
    :param msg: Descriptive message for the error (other than HTTP reason).
    :param err_type: Error/Exception type for better specifying error as defined in API.
    :param payload: JSON data to send to client as dict.
    :param kwargs: Extra arguments.
    :return: A Response object.
    """
    err_dict = kwargs
    err_dict['message'] = msg

    if err_type is not None:
        err_dict["type"] = err_type

    if payload is not None:
        for key, value in payload.items():
            err_dict[key] = value

    response = jsonify(err_dict)
    response.status = status
    return response


__all__ = ['make_error']