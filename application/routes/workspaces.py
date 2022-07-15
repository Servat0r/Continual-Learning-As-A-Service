from __future__ import annotations

from flask import Blueprint
from http import HTTPStatus

from application.errors import *
from application.utils import *
from application.validation import *

from application.resources.contexts import UserWorkspaceResourceContext
from application.models import User, Workspace

from .auth import *


workspaces_bp = Blueprint('workspaces', __name__, url_prefix='/users/<user:username>/workspaces')


@linker.args_rule('Workspace')
def workspace_args(workspace: Workspace):
    return {
        'username': workspace.get_owner().get_name(),
        'wname': workspace.get_name(),
    }


@linker.args_rule('Workspaces')
def workspaces_args(user: User):
    return {'username': user.get_name()}


@workspaces_bp.post('/')
@workspaces_bp.post('')
@token_auth.login_required
@check_json(False, required={'name'})
@check_ownership(msg="You cannot create a workspace for another user ({user}).", eval_args={'user': 'username'})
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
    data, opts, extras = get_check_json_data()
    current_user = token_auth.current_user()
    wname = data['name']
    result, msg = validate_workspace_resource_experiment(wname)
    if not result:
        return InvalidResourceName(payload={'resource_name': wname})
    workspace = Workspace.create(data['name'], current_user)
    if workspace:
        data = linker.make_links(workspace.to_dict())
        return make_success_dict(HTTPStatus.CREATED, data=data)
    else:
        return InternalFailure(msg=f"Failed to create workspace '{data['name']}'.")


@workspaces_bp.get('/<workspace:wname>/')
@workspaces_bp.get('/<workspace:wname>')
@token_auth.login_required
@linker.link_rule('Workspace', blueprint=workspaces_bp)
@check_ownership(msg="You cannot retrieve another user ({user}) workspace data.", eval_args={'user': 'username'})
def get_workspace(username, wname):
    user = User.get_by_name(username)
    if not user:
        return NotExistingUser(user=username)
    context = UserWorkspaceResourceContext(username, wname)
    urn = Workspace.dfl_claas_urn_builder(context)
    workspace = Workspace.get_by_claas_urn(urn)
    if workspace is not None:
        data = linker.make_links(workspace.to_dict())
        return make_success_dict(HTTPStatus.OK, data=data)
    else:
        return ResourceNotFound(resource=wname)


@workspaces_bp.get('/')
@workspaces_bp.get('')
@token_auth.login_required
@linker.link_rule('Workspaces', blueprint=workspaces_bp)
@check_ownership(msg="You cannot retrieve another user ({user}) workspaces data.", eval_args={'user': 'username'})
def get_workspaces(username):
    user = User.get_by_name(username)
    if not user:
        return NotExistingUser(user=username)
    data = {}
    for workspace in Workspace.get_by_owner(t.cast(User, user)):
        data[workspace.name] = linker.make_links(workspace.to_dict())
    return make_success_dict(HTTPStatus.OK, data=data)


@workspaces_bp.patch('/<workspace:wname>/name/')
@workspaces_bp.patch('/<workspace:wname>/name')
@token_auth.login_required
@check_json(False, required={'new_name'})
@check_ownership(msg="You cannot rename another user ({user}) workspace.", eval_args={'user': 'username'})
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
    data, opts, extras = get_check_json_data()
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
@check_ownership(msg="You cannot delete another user workspace ({user})!", eval_args={'user': 'username'})
def delete_workspace(username, wname):
    context = UserWorkspaceResourceContext(username, wname)
    urn = Workspace.dfl_claas_urn_builder(context)
    workspace = Workspace.get_by_claas_urn(urn)
    if not workspace:
        return ResourceNotFound(resource=wname)
    result, ex = workspace.delete()
    if result:
        return make_success_dict()
    else:
        return InternalFailure(msg=ex.args[0], exception=str(ex))


@workspaces_bp.get('<workspace:wname>/status/')
@workspaces_bp.get('<workspace:wname>/status')
@token_auth.login_required
@check_ownership(msg="You cannot get another user ({user}) workspace", eval_args={'user': 'username'})
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
@check_json(False, required={'status'})
@check_ownership(msg="You cannot set the status of another user ({user}) workspace!", eval_args={'user': 'username'})
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
    data, opts, extras = get_check_json_data()
    context = UserWorkspaceResourceContext(username, wname)
    urn = Workspace.dfl_claas_urn_builder(context)
    workspace = Workspace.get_by_claas_urn(urn)
    if not workspace:
        return ResourceNotFound(resource=wname)
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
    'workspace_args',

    'create_workspace',
    'get_workspace',
    'get_workspaces',

    'rename_workspace',
    'delete_workspace',
    'get_workspace_status',
    'set_workspace_status',
]