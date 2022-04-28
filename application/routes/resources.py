"""
Base module for handling operations on "generic" resources.
"""
import os
from http import HTTPStatus
from flask import request

from application.utils import *
from application.errors import *
from application.resources.contexts import *
from application.mongo.resources import MongoResourceConfig
from .auth import check_current_user_ownership


__DEBUG = bool(os.environ.get('DEBUG') or False)

UnknownResourceType = ServerResponseError(
    HTTPStatus.NOT_FOUND,
    'UnknownResourceType',
    "Unknown resource type: '{type}'.",
    1,
)


def add_new_resource(username, workspace, typename):
    """
    Base method for adding a new "generic" resource.
    :param username:
    :param workspace:
    :param typename:
    :return:
    """
    if not check_current_user_ownership(username):
        return ForbiddenOperation(f"You cannot add a new {typename} for another user ({username}).")

    data, error, opts, extras = checked_json(request, True, {'name', 'build'}, {'description'})
    if error:
        if data:
            return error(**data)
        else:
            return error()
    else:
        context = DictUserWorkspaceResourceContext(username, workspace)

        dtype = DataType.get_type(typename)
        if dtype is None:
            return UnknownResourceType(type=typename)

        ctp = t.cast(ReferrableDataType, dtype).config_type()
        if ctp is None:
            return InternalFailure(msg=f"Unknown config type '{typename}' for building resource.")

        resource_document = ctp.create(data, context)
        if resource_document is None:
            return InternalFailure(
                msg=f"Failed to create resource document for resource '{data['name']}' of type {typename}."
            )
        elif __DEBUG:
            print(resource_document)
        return make_success_dict(msg=f"Successfully created resource of type '{typename}'!")


def build_resource(username, workspace, typename, name):
    """
    Base method for building a "generic" resource.
    TODO NO JSON!
    TODO All parameters must be retrieved from URL!
    :param username:
    :param workspace:
    :param typename:
    :param name:
    :return:
    """
    if not check_current_user_ownership(username):
        return ForbiddenOperation(f"You cannot add a new {typename} for another user ({username}).")

    context = DictUserWorkspaceResourceContext(username, workspace)

    dtype = DataType.get_type(typename)
    if dtype is None:
        return UnknownResourceType(type=typename)

    ctp: t.Type[MongoResourceConfig] = t.cast(ReferrableDataType, dtype).config_type()
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

    resource = resource_document.build(context)
    if resource is not None:
        if __DEBUG:
            print(resource)
        return make_success_dict(msg=f"Successfully built resource '{name}'.")
    else:
        return InternalFailure(msg=f"Failed to build resource '{name}'.")


def delete_resource(username, workspace, typename, name):
    """
    TODO NO JSON!
    TODO All parameters must be retrieved from URL!
    :param username:
    :param workspace:
    :param typename:
    :param name:
    :return:
    """
    if not check_current_user_ownership(username):
        return ForbiddenOperation(f"You cannot add a new {typename} for another user ({username}).")

    context = DictUserWorkspaceResourceContext(username, workspace)

    dtype = DataType.get_type(typename)
    if dtype is None:
        return UnknownResourceType(type=typename)

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
        resource_document.delete(context)
        return make_success_dict(msg=f"Successfully deleted resource '{name}'.")
    except Exception as ex:
        return InternalFailure(msg=ex.args[0])