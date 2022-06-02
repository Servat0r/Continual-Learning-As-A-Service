from __future__ import annotations

from flask import Blueprint, request
from http import HTTPStatus

from application.errors import *
from application.utils import *
from application.validation import *

from application.resources.contexts import UserWorkspaceResourceContext
from application.models import User, Workspace

from .auth import token_auth, check_current_user_ownership


workspaces_bp = Blueprint('workspaces', __name__, url_prefix='/users/<user:username>/workspaces')


@workspaces_bp.post('/')
@workspaces_bp.post('')
@token_auth.login_required
def create_workspace(username):
    """
    RequestSyntax:

    {
        "name": "<name>"
    }

    ResponseSyntax:
    status: 201 created
    {
        "name": "<name>"
    }

    :param username:
    :return:
    """
    data, error, opts, extras = checked_json(request, False, {'name'})
    if error:
        if data:
            return error(**data)
        else:
            return error()

    current_user = token_auth.current_user()

    if current_user.username != username:
        return ForbiddenOperation(msg="You cannot create a workspace for another user!")

    wname = data['name']
    result, msg = validate_workspace_resource_experiment(wname)
    if not result:
        return InvalidResourceName(payload={'resource_name': wname})

    workspace = Workspace.create(data['name'], current_user)
    if workspace:
        return make_success_dict(HTTPStatus.CREATED, data=workspace.to_dict())
    else:
        return InternalFailure(msg=f"Failed to create workspace '{data['name']}'.")


@workspaces_bp.get('/<workspace:wname>/')
@workspaces_bp.get('/<workspace:wname>')
@token_auth.login_required
def get_workspace(username, wname):
    user = User.get_by_name(username)
    if not user:
        return NotExistingUser(user=username)
    context = UserWorkspaceResourceContext(username, wname)
    urn = Workspace.dfl_claas_urn_builder(context)
    data = Workspace.get_by_claas_urn(urn).to_dict()
    if data is None:
        return ResourceNotFound(resource=wname)
    else:
        return make_success_dict(HTTPStatus.OK, data=data)


@workspaces_bp.get('/')
@workspaces_bp.get('')
@token_auth.login_required
def get_workspaces(username):
    user = User.get_by_name(username)
    if not user:
        return NotExistingUser(user=username)
    data = {}
    for workspace in Workspace.get_by_owner(t.cast(User, user)):
        data[workspace.name] = workspace.to_dict()
    return make_success_dict(HTTPStatus.OK, data=data)


@workspaces_bp.patch('/<workspace:wname>/name/')
@workspaces_bp.patch('/<workspace:wname>/name')
@token_auth.login_required
def rename_workspace(username, wname):
    """
    RequestSyntax:
    {
        "new_name": <new_name>
    }
    :param username:
    :param wname:
    :return:
    """
    result, error = check_current_user_ownership(username,
                                                 f"You cannot rename another user ({username}) workspace ({wname}).")
    if not result:
        return error

    data, error, opts, extras = checked_json(request, False, {'new_name'})
    if error:
        if data:
            return error(**data)
        else:
            return error()
    else:
        context = UserWorkspaceResourceContext(username, wname)
        urn = Workspace.dfl_claas_urn_builder(context)
        workspace = Workspace.get_by_claas_urn(urn)

        new_name = data['new_name']
        result, msg = validate_workspace_resource_experiment(new_name)
        if not result:
            return InvalidResourceName(payload={'resource_name': new_name})

        result, msg = workspace.rename(wname, new_name)
        if not result:
            return InternalFailure(msg=msg)
        else:
            return make_success_dict(data={'old_name': wname, 'new_name': new_name})


@workspaces_bp.delete('/<workspace:wname>/')
@workspaces_bp.delete('/<workspace:wname>')
@token_auth.login_required
def delete_workspace(username, wname):

    current_user = token_auth.current_user()
    context = UserWorkspaceResourceContext(username, wname)
    urn = Workspace.dfl_claas_urn_builder(context)
    workspace = Workspace.get_by_claas_urn(urn)

    if not workspace:
        return ResourceNotFound(resource=wname)

    if (current_user.username != username) or (workspace.owner.username != username):
        return ForbiddenOperation(msg="You cannot delete another user's workspace!")

    result, ex = workspace.delete()
    if result:
        return make_success_dict()
    else:
        return InternalFailure(msg=ex.args[0], exception=str(ex))


@workspaces_bp.get('<workspace:wname>/status/')
@workspaces_bp.get('<workspace:wname>/status')
@token_auth.login_required
def get_workspace_status(username, wname):
    user = User.get_by_name(username)
    if not user:
        return NotExistingUser(user=username)

    context = UserWorkspaceResourceContext(username, wname)
    urn = Workspace.dfl_claas_urn_builder(context)
    workspace = Workspace.get_by_claas_urn(urn)
    if not workspace:
        return ResourceNotFound(resource=wname)

    return make_success_dict(data={'status': workspace.status})


@workspaces_bp.patch('<workspace:wname>/status/')
@workspaces_bp.patch('<workspace:wname>/status')
@token_auth.login_required
def set_workspace_status(username, wname):
    """
    RequestSyntax:

    {
        "status": "OPEN"/"CLOSED"
    }

    ResponseSyntax:

    {
        "status": "OPEN"/"CLOSED"
    }

    :param username:
    :param wname:
    :return:
    """

    data, error, opts, extras = checked_json(request, False, {'status'})
    if error:
        if data:
            return error(**data)
        else:
            return error()

    current_user = token_auth.current_user()
    context = UserWorkspaceResourceContext(username, wname)
    urn = Workspace.dfl_claas_urn_builder(context)
    workspace = Workspace.get_by_claas_urn(urn)

    if not workspace:
        return ResourceNotFound(resource=wname)

    if (current_user.username != username) or (workspace.owner.id != current_user.id):
        return ForbiddenOperation(msg="You cannot set the status of another user's workspace!")

    status = data['status']
    if status == Workspace.OPEN:
        workspace.open()
    elif status == Workspace.CLOSED:
        workspace.close()
    else:
        return InvalidParameterValue(parameter=status)
    return make_success_dict(data={'status': workspace.status})


__all__ = [
    'workspaces_bp',
    'create_workspace',
    'get_workspace',
    'get_workspaces',
    'rename_workspace',
    'delete_workspace',
    'get_workspace_status',
    'set_workspace_status',
]