"""
Custom errors implementation as described in "docs/CLaaS API Errors.pdf".
"""
from __future__ import annotations
from http import HTTPStatus
from flask import Response

from .utils import *


class ServerResponseError(object):
    """
    Base class for defining server response errors.
    """

    def __init__(self, status: int, name: str, dfl_msg: str, fmt_len: int = 0):
        """
        :param status: HTTP status code of the error.
        :param name: Name of the error.
        :param dfl_msg: Default message to be sent with this error.
        """
        if fmt_len < 0:
            raise ValueError(f"Invalid fmt_len = {fmt_len}.")
        self.status = status
        self.name = name
        self.dfl_msg = dfl_msg
        self.fmt_len = fmt_len

    def __call__(self, msg: str | None = None, **kwargs) -> Response:
        """
        Returns an instance of this error with the specified message, or the default one if not specified.
        :param msg: Custom error message to send.
        :return: A Response object encapsulating the error.
        """
        if msg is None:
            msg = self.dfl_msg
            if self.fmt_len > 0:
                if kwargs is None:
                    raise ValueError("Missing format parameters.")
                elif len(kwargs) != self.fmt_len:
                    raise ValueError(f"Insufficient format parameters ({self.fmt_len} expected, {len(kwargs)} given).")
                else:
                    return make_error(self.status, msg.format(**kwargs), err_type=self.name)
        return make_error(self.status, msg, err_type=self.name)


# Authentication Errors 401
InvalidToken = ServerResponseError(
    HTTPStatus.UNAUTHORIZED,
    'InvalidToken',
    "The request must contain a valid authentication token.",
)

ExpiredToken = ServerResponseError(
    HTTPStatus.UNAUTHORIZED,
    'ExpiredToken',
    "Authentication token is expired.",
)

MissingToken = ServerResponseError(
    HTTPStatus.UNAUTHORIZED,
    'MissingToken',
    "Authentication token is missing.",
)

# Authorization Errors 403
PermissionDenied = ServerResponseError(
    HTTPStatus.FORBIDDEN,
    'PermissionDenied',
    "You do not have sufficient access to perform this action.",
)

ForbiddenOperation = ServerResponseError(
    HTTPStatus.FORBIDDEN,
    'ForbiddenOperation',
    "The operation cannot be performed.",
)

# Syntax Errors 400
BadJSONSyntax = ServerResponseError(
    HTTPStatus.BAD_REQUEST,
    'BadJSONSyntax',
    "The request body is not in a correct JSON format.",
)

BadRequestSyntax = ServerResponseError(
    HTTPStatus.BAD_REQUEST,
    'BadRequestSyntax',
    "The request syntax is incorrect.",
)

MalformedQueryString = ServerResponseError(
    HTTPStatus.BAD_REQUEST,
    'MalformedQueryString',
    "The query string contains a syntax error.",
)

MissingParameter = ServerResponseError(
    HTTPStatus.BAD_REQUEST,
    'MissingParameter',
    "Missing parameter '{parameter}'.",
    fmt_len=1,
)

# Validation Errors 400, 404
InvalidUsername = ServerResponseError(
    HTTPStatus.BAD_REQUEST,
    'InvalidUsername',
    "The username provided is invalid.",
)

InvalidEmail = ServerResponseError(
    HTTPStatus.BAD_REQUEST,
    'InvalidEmail',
    "The email provided is invalid.",
)

InvalidPassword = ServerResponseError(
    HTTPStatus.BAD_REQUEST,
    'InvalidPassword',
    f"Password must be of at least 8 characters and contain at least" +
    f" a digit, a lowercase character, an uppercase character and a special character" +
    f" among '$', '%', '&', '?', '@' and '#'.",
)

InvalidParameterCombination = ServerResponseError(
    HTTPStatus.BAD_REQUEST,
    'InvalidParameterCombination',
    "Parameters that must not be used together were used together.",
)

InvalidParameterValue = ServerResponseError(
    HTTPStatus.BAD_REQUEST,
    'InvalidParameterValue',
    "Invalid value for the parameter '{parameter}'.",
    fmt_len=1,
)

InvalidParameter = ServerResponseError(
    HTTPStatus.BAD_REQUEST,
    'InvalidParameter',
    "Unknown parameter '{parameter}'.",
    fmt_len=1,
)

InvalidQueryParameter = ServerResponseError(
    HTTPStatus.BAD_REQUEST,
    'InvalidQueryParameter',
    "Unknown query parameter '{parameter}'.",
    fmt_len=1,
)

NotExistingUser = ServerResponseError(
    HTTPStatus.NOT_FOUND,
    'NotExistingUser',
    "The user '{user}' does not exist.",
    fmt_len=1,
)

ExistingUser = ServerResponseError(
    HTTPStatus.NOT_FOUND,
    'ExistingUser',
    "The user '{user}' already exists.",
    fmt_len=1,
)

ResourceNotFound = ServerResponseError(
    HTTPStatus.NOT_FOUND,
    'ResourceNotFound',
    "Resource '{resource}' not found.",
    fmt_len=1,
)

# Server Errors 500, 503
InternalFailure = ServerResponseError(
    HTTPStatus.INTERNAL_SERVER_ERROR,
    'InternalFailure',
    "The request processing has failed because of an unknown error, exception or failure.",
)

ServiceUnavailable = ServerResponseError(
    HTTPStatus.SERVICE_UNAVAILABLE,
    'ServiceUnavailable',
    "The request has failed due to a temporary failure of the server.",
)


RouteNotImplemented = ServerResponseError(
    HTTPStatus.NOT_IMPLEMENTED,
    'NotImplemented',
    "Request handler is not yet implemented."
)

__all__ = [
    'ServerResponseError',
    'InvalidToken',
    'ExpiredToken',
    'MissingToken',
    'PermissionDenied',
    'ForbiddenOperation',
    'BadJSONSyntax',
    'BadRequestSyntax',
    'MalformedQueryString',
    'MissingParameter',
    'InvalidUsername',
    'InvalidEmail',
    'InvalidPassword',
    'InvalidParameterCombination',
    'InvalidParameterValue',
    'InvalidParameter',
    'InvalidQueryParameter',
    'NotExistingUser',
    'ExistingUser',
    'ResourceNotFound',
    'InternalFailure',
    'ServiceUnavailable',
    'RouteNotImplemented',
]
