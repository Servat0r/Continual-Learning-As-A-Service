"""
Base module for handling operations on "generic" resources.
"""
from __future__ import annotations
from http import HTTPStatus
from flask import request, Response

from application.utils import *
from application.errors import *
from application.resources import *

from application.mongo.resources import MongoResourceConfig
from .auth import check_current_user_ownership


__DEBUG = bool(os.environ.get('DEBUG', False))

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


def add_new_resource(username, workspace, typename: str | t.Type[DataType]) -> Response:
    """
    Base method for adding a new "generic" resource.
    :param username:
    :param workspace:
    :param typename:
    :return:
    """
    result, error = check_current_user_ownership(username,
                                                 f"You cannot add a new {typename} for another user ({username}).")
    if not result:
        return error

    data, error, opts, extras = checked_json(request, True, {'name', 'build'}, {'description'})
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
        elif __DEBUG:
            pass
            # print(resource_document)
        return make_success_dict(HTTPStatus.CREATED, msg=f"Successfully created resource of type '{typename}'!")


def build_resource(username, workspace, typename: str | t.Type[DataType], name) -> Response:
    """
    Base method for building a "generic" resource.
    :param username:
    :param workspace:
    :param typename:
    :param name:
    :return:
    """
    result, error = check_current_user_ownership(username,
                                                 f"You cannot build a {typename} for another user ({username}).")
    if not result:
        return error

    context = UserWorkspaceResourceContext(username, workspace)

    dtype, error = _canonicalize_datatype(typename)
    if error:
        return error

    ctp: t.Type[MongoResourceConfig] = t.cast(ReferrableDataType, dtype).config_type()
    if ctp is None:
        return InternalFailure(msg=f"Unknown config type '{typename}' for building resource.")

    uri = ctp.dfl_uri_builder(context, name)
    resource_document = ctp.get_by_uri(uri)

    if resource_document is None:
        return InternalFailure(
            msg=f"Failed to build resource document for resource '{name}' of type {typename}."
        )
    elif __DEBUG:
        print(resource_document)

    resource = resource_document.build(context)
    if resource is not None:
        if __DEBUG:
            print(resource)
        return make_success_dict(msg=f"Successfully built resource '{name}'.")
    else:
        return InternalFailure(msg=f"Failed to build resource '{name}'.")


def get_resource(username, workspace, typename: str | t.Type[DataType], name, ownership_fail_msg: str = None,
                 **ownership_fail_args) -> tuple[MongoResourceConfig | None, Response | None]:

    ownership_fail_msg = ForbiddenOperation.dfl_msg if ownership_fail_msg is None else ownership_fail_msg
    result, error = check_current_user_ownership(username, ownership_fail_msg, **ownership_fail_args)
    if not result:
        return None, error

    dtype, error = _canonicalize_datatype(typename)
    if error:
        return None, error

    resource: MongoResourceConfig = t.cast(ReferrableDataType, dtype).config_type().get_one(username, workspace, name)
    if resource is not None:
        return resource, None
    else:
        return None, ResourceNotFound(resource=name)


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
    result, error = check_current_user_ownership(username,
                                                 f"You cannot update a {typename} for another user ({username}).")
    if not result:
        return error

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
    elif __DEBUG:
        print(resource_document)

    resource_document = resource_document[0]
    print(f"updata = {updata}, context = {context}")
    result, msg = resource_document.update(updata, context)
    if not result:
        return InternalFailure(msg=msg)
    else:
        return make_success_dict()


def delete_resource(username, workspace, typename: str | t.Type[DataType], name) -> Response:
    """
    :param username:
    :param workspace:
    :param typename:
    :param name:
    :return:
    """
    result, error = check_current_user_ownership(username,
                                                 f"You cannot delete a {typename} for another user ({username}).")
    if not result:
        return error

    context = UserWorkspaceResourceContext(username, workspace)

    dtype, error = _canonicalize_datatype(typename)
    if error:
        return error

    ctp: MongoResourceConfig = t.cast(ReferrableDataType, dtype).config_type()
    if ctp is None:
        return InternalFailure(msg=f"Unknown config type '{typename}' for building resource.")

    uri = ctp.dfl_uri_builder(context, name)
    resource_document = ctp.get_by_uri(uri)
    if __DEBUG:
        print(uri, resource_document, sep='\n')

    if resource_document is None:
        return InternalFailure(
            msg=f"Failed to build resource document for resource '{name}' of type {typename}."
        )
    elif __DEBUG:
        print(resource_document)

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