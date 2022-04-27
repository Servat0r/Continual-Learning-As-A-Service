from flask import Blueprint, request
from application.routes.auth import token_auth
from http import HTTPStatus
from application.errors import *
from application.utils import *
from application.resources.contexts import *
from application.models import User, Workspace


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
        return ForbiddenOperation("You cannot create a workspace for another user!")

    workspace = Workspace.create(data['name'], current_user)
    return make_success_dict(HTTPStatus.CREATED, data=workspace.to_dict())


@workspaces_bp.get('/<workspace:wname>/')
@workspaces_bp.get('/<workspace:wname>')
@token_auth.login_required
def get_workspace(username, wname):
    user = User.get_by_name(username)
    if not user:
        return NotExistingUser(user=username)
    context = DictUserWorkspaceResourceContext(username, wname)
    uri = Workspace.dfl_uri_builder(context)
    data = Workspace.get_by_uri(uri).to_dict()
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


@workspaces_bp.delete('/<workspace:wname>/')
@workspaces_bp.delete('/<workspace:wname>')
@token_auth.login_required
def delete_workspace(username, wname):

    current_user = token_auth.current_user()
    context = DictUserWorkspaceResourceContext(username, wname)
    uri = Workspace.dfl_uri_builder(context)
    workspace = Workspace.get_by_uri(uri)

    if not workspace:
        return ResourceNotFound(resource=wname)

    if (current_user.username != username) or (workspace.owner.username != username):
        return ForbiddenOperation("You cannot delete another user's workspace!")

    workspace.delete()
    return make_success_dict()


@workspaces_bp.get('<workspace:wname>/status/')
@workspaces_bp.get('<workspace:wname>/status')
@token_auth.login_required
def get_workspace_status(username, wname):
    user = User.get_by_name(username)
    if not user:
        return NotExistingUser(user=username)

    context = DictUserWorkspaceResourceContext(username, wname)
    uri = Workspace.dfl_uri_builder(context)
    workspace = Workspace.get_by_uri(uri)
    if not workspace:
        return ResourceNotFound(resource=wname)

    return {'status': workspace.status}


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
    context = DictUserWorkspaceResourceContext(username, wname)
    uri = Workspace.dfl_uri_builder(context)
    workspace = Workspace.get_by_uri(uri)

    if not workspace:
        return ResourceNotFound(resource=wname)

    if (current_user.username != username) or (workspace.owner.id != current_user.id):
        return ForbiddenOperation("You cannot set the status of another user's workspace!")

    status = data['status']
    if status == Workspace.OPEN:
        workspace.open()
    elif status == Workspace.CLOSED:
        workspace.close()
    else:
        return InvalidParameterValue(parameter=status)
    return make_success_dict(data={'status': workspace.status})


@workspaces_bp.get('/<workspace:wname>/requirements/')
@workspaces_bp.get('/<workspace:wname>/requirements')
@token_auth.login_required
def get_workspace_requirements(username, wname):    # TODO Completare!
    """

    :param username:
    :param wname:
    :return:
    """

    current_user = token_auth.current_user()
    workspace = Workspace.get_by_name(wname)

    if not workspace:
        return ResourceNotFound(resource=wname)

    if (current_user.username != username) or (workspace.owner_id != current_user.id):
        return ForbiddenOperation("You cannot get workspace requirements for another user's workspace!")

    requirements = {'message': 'NotImplemented'}
    return make_success_kwargs(requirements=requirements)