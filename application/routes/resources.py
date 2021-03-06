"""
Base module for handling operations on "generic" resources.
"""
from __future__ import annotations
from http import HTTPStatus
from flask import Response

from application.utils import *
from application.errors import *
from application.resources import *

from application.mongo.resources import MongoResourceConfig
from .auth import *


UnknownResourceType = ServerResponseError(
    HTTPStatus.NOT_FOUND,
    'UnknownResourceType',
    "Unknown resource type: '{type}'.",
    1,
)


def _canonicalize_datatype(tp: str | t.Type[DataType]) -> \
        tuple[t.Optional[t.Type[DataType]], t.Optional[Response]]:
    if isinstance(tp, str):
        return DataType.get_type(tp), None
    elif issubclass(tp, DataType):
        return tp, None
    else:
        return None, UnknownResourceType(type=str(tp))


@tuple_check_ownership(msg="You cannot add a new {type} for another user ({user}).",
                       eval_args={'type': 'typename', 'user': 'username'})
def add_new_resource(username, workspace, typename: str | t.Type[DataType], required=None) -> Response:
    """
    Base method for adding a new "generic" resource.
    :param username:
    :param workspace:
    :param typename:
    :param required:
    :return:
    """
    required = {'name', 'build'} if required is None else required
    data, error, opts, extras = checked_json(True, required, {'description'})
    if error:
        if data:
            return error(**data)
        else:
            return error()
    else:
        context = UserWorkspaceResourceContext(username, workspace)

        dtype, error = _canonicalize_datatype(typename)
        if error:
            return error

        ctp = t.cast(ReferrableDataType, dtype).config_type()
        if ctp is None:
            return InternalFailure(msg=f"Unknown config type '{typename}' for building resource.")

        resource_document = ctp.create(data, context)
        if resource_document is None:
            return InternalFailure(
                msg=f"Failed to create resource document for resource '{data['name']}' of type {typename}."
            )
        return make_success_dict(HTTPStatus.CREATED, msg=f"Successfully created resource of type '{typename}'!")


@tuple_check_ownership(msg="You cannot build a {type} for another user ({user}).",
                       eval_args={'type': 'typename', 'user': 'username'})
def build_resource(username, workspace, typename: str | t.Type[DataType], name) -> Response:
    """
    Base method for building a "generic" resource.
    :param username:
    :param workspace:
    :param typename:
    :param name:
    :return:
    """
    context = UserWorkspaceResourceContext(username, workspace)
    dtype, error = _canonicalize_datatype(typename)
    if error:
        return error

    ctp: t.Type[MongoResourceConfig] = t.cast(ReferrableDataType, dtype).config_type()
    if ctp is None:
        return InternalFailure(msg=f"Unknown config type '{typename}' for building resource.")

    urn = ctp.dfl_claas_urn_builder(context, name)
    resource_document = ctp.get_by_claas_urn(urn)

    if resource_document is None:
        return InternalFailure(
            msg=f"Failed to build resource document for resource '{name}' of type {typename}."
        )
    resource = resource_document.build(context)
    if resource is not None:
        return make_success_dict(msg=f"Successfully built resource '{name}'.")
    else:
        return InternalFailure(msg=f"Failed to build resource '{name}'.")


@tuple_check_ownership(msg="You cannot retrieve another user ({user}) {type}",
                       eval_args={'user': 'username', 'type': 'typename'})
def get_resource(username, workspace, typename: str | t.Type[DataType], name: str = None,
                 **args) -> tuple[MongoResourceConfig | None, Response | None]:
    dtype, error = _canonicalize_datatype(typename)
    if error:
        return None, error
    # noinspection PyUnresolvedReferences
    resource: MongoResourceConfig = dtype.config_type().get_one(username, workspace, name, **args)
    if resource is not None:
        return resource, None
    else:
        return None, ResourceNotFound(resource=name)


@tuple_check_ownership(msg="You cannot update a {type} for another user ({user}).",
                       eval_args={'type': 'typename', 'user': 'username'})
def update_resource(username, workspace, typename: str | t.Type[DataType], name, updata) -> Response:
    """
    Updates a resource.
    :param username:
    :param workspace:
    :param typename:
    :param name:
    :param updata:
    :return:
    """
    dtype, error = _canonicalize_datatype(typename)
    if error:
        return error

    ctp: t.Type[MongoResourceConfig] = t.cast(ReferrableDataType, dtype).config_type()
    if ctp is None:
        return InternalFailure(msg=f"Unknown config type '{typename}' for building resource.")
    context = UserWorkspaceResourceContext(username, workspace)

    resource_document = ctp.get(username, workspace, name)
    if resource_document is None or len(resource_document) != 1:
        return InternalFailure(
            msg=f"Failed to retrieve resource document for resource '{name}' of type {typename}."
        )
    resource_document = resource_document[0]
    result, msg = resource_document.update(updata, context)
    if not result:
        return InternalFailure(msg=msg)
    else:
        return make_success_dict()


@tuple_check_ownership(msg="You cannot delete a {type} for another user ({user}).",
                       eval_args={'type': 'typename', 'user': 'username'})
def delete_resource(username, workspace, typename: str | t.Type[DataType], name) -> Response:
    """
    :param username:
    :param workspace:
    :param typename:
    :param name:
    :return:
    """
    context = UserWorkspaceResourceContext(username, workspace)
    dtype, error = _canonicalize_datatype(typename)
    if error:
        return error

    ctp: MongoResourceConfig = t.cast(ReferrableDataType, dtype).config_type()
    if ctp is None:
        return InternalFailure(msg=f"Unknown config type '{typename}' for building resource.")

    urn = ctp.dfl_claas_urn_builder(context, name)
    resource_document = ctp.get_by_claas_urn(urn)
    if resource_document is None:
        return InternalFailure(
            msg=f"Failed to build resource document for resource '{name}' of type {typename}."
        )
    try:
        result, ex = resource_document.delete(context)
        if result:
            return make_success_dict(msg=f"Successfully deleted resource '{name}'.")
        else:
            raise ex
    except Exception as ex:
        return InternalFailure(msg=ex.args[0], exception=str(ex))


__all__ = [
    'add_new_resource',
    'build_resource',
    'get_resource',
    'update_resource',
    'delete_resource',
]