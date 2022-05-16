from flask import Blueprint, request

from application.errors import *
from application.utils import checked_json, make_success_dict
from application.models import Workspace

from .auth import token_auth, check_current_user_ownership
from application.data_managing import BaseDataRepository


data_repositories_bp = Blueprint('data_repositories', __name__,
                                 url_prefix='/users/<user:username>/workspaces/<workspace:wname>/data')


@data_repositories_bp.post('/')
@data_repositories_bp.post('')
@token_auth.login_required
def create_data_repository(username, wname):
    """
    RequestSyntax:
    {
        "name": <name>,
        "description": <description>
    }
    :param username:
    :param wname:
    :return:
    """
    result, error = check_current_user_ownership(username,
                                                 f"You cannot create a data repository for another user ({username}).")
    if not result:
        return error

    data, error, opts, extras = checked_json(request, False, {'name'}, {'description'})
    if error:
        if data:
            return error(**data)
        else:
            return error()

    workspace = Workspace.canonicalize((username, wname))
    name = data['name']
    description = data.get('description')

    data_repository = BaseDataRepository.create(name, workspace, desc=description)
    if data_repository:
        return make_success_dict(data=data_repository.to_dict())
    else:
        return InternalFailure(msg=f"Failed to create data repository '{name}'.")


@data_repositories_bp.delete('/<name>/')
@data_repositories_bp.delete('/<name>')
@token_auth.login_required
def delete_repo(username, wname, name):

    result, error = check_current_user_ownership(username,
                                                 f"You cannot delete another user ('{username}') data repository.")
    if not result:
        return error

    current_user = token_auth.current_user()
    workspace = Workspace.canonicalize((current_user, wname))
    data_repository = BaseDataRepository.get_one(workspace, name)

    if data_repository:
        result, exc = data_repository.delete()
        if result:
            return make_success_dict(msg=f"Data repository '{name}' successfully deleted.")
        else:
            return InternalFailure(msg=exc.args[0], exception=str(exc))
    else:
        return ResourceNotFound(resource=name)


@data_repositories_bp.get('/<name>/')
@data_repositories_bp.get('/<name>')
@token_auth.login_required
def get_data_repo(username, wname, name):
    result, error = check_current_user_ownership(username,
                                                 f"You cannot create a data repository for another user ({username}).")
    if not result:
        return error

    current_user = token_auth.current_user()
    workspace = Workspace.canonicalize((current_user, wname))
    data_repository = BaseDataRepository.get_one(workspace, name)

    if data_repository:
        return make_success_dict(data=data_repository.to_dict())
    else:
        return ResourceNotFound(resource=name)


@data_repositories_bp.get('/<name>/desc/')
@data_repositories_bp.get('/<name>/desc')
@token_auth.login_required
def get_data_repo_desc(username, wname, name):
    result, error = check_current_user_ownership(username,
                                                 f"You cannot create a data repository for another user ({username}).")
    if not result:
        return error

    current_user = token_auth.current_user()
    workspace = Workspace.canonicalize((current_user, wname))
    data_repository = BaseDataRepository.get_one(workspace, name)

    if data_repository:
        desc = data_repository.get_description()
        return make_success_dict(data={'description': desc})
    else:
        return ResourceNotFound(resource=name)


@data_repositories_bp.post('/<name>/folders/')
@data_repositories_bp.post('/<name>/folders')
@token_auth.login_required
def create_sub_folder(username, wname, name):
    """
    RequestSyntax:
    {
        "name": <folder_name>,
        "path": <folder_path> (separated by '/')
    }
    :param username:
    :param wname:
    :param name:
    :return:
    """
    result, error = check_current_user_ownership(username,
                                                 f"You cannot create a folder in another user ({username}) repository.")
    if not result:
        return error

    data, error, opts, extras = checked_json(request, False, {'name'}, {'path'})
    if error:
        return error(**data) if data else error()

    folder_name = data['name']
    folder_path = data.get('path')

    if (folder_path is not None) and not isinstance(folder_path, str):
        return BadRequestSyntax(msg=f"'folder_path' must be a string!")

    folders = folder_path.split('/') if folder_path is not None else None

    folders = [val for val in folders if len(val) > 0]

    workspace = Workspace.canonicalize((username, wname))
    data_repository = BaseDataRepository.get_one(workspace, name)
    if data_repository:
        result, exc = data_repository.add_directory(folder_name, folders)
        if result:
            return make_success_dict()
        else:
            return InternalFailure(msg=exc.args[0])
    else:
        return ResourceNotFound(resource=name)


@data_repositories_bp.patch('/<name>/folders/')
@data_repositories_bp.patch('/<name>/folders')
@token_auth.login_required
def move_folder(username, wname, name):
    """
    RequestSyntax:
    {
        "src_path": <source_path>,  # absolute!
        "dest_path": <dest_path>    # absolute!
    }
    NOTE: dest_path CANNOT be a location contained in src_path (e.g., it CANNOT be:
        src_path = 'a/b/c/d'
        dest_path = 'a/b'
    ).
    :param username:
    :param wname:
    :param name:
    :return:
    """
    result, error = check_current_user_ownership(username,
                                                 f"You cannot create a folder in another user ({username}) repository.")
    if not result:
        return error

    data, error, opts, extras = checked_json(request, False, {'src_path', 'dest_path'})
    if error:
        return error(**data) if data else error()

    src_path = data['src_path'].split('/')
    dest_path = data['dest_path'].split('/')

    if len(src_path) < 1 or len(dest_path) < 1:
        return BadRequestSyntax(msg="Source and destination paths must have at least one item!")

    src_parents = src_path[:-1]
    dest_parents = dest_path[:-1]
    src_name = src_path[-1]
    dest_name = dest_path[-1]

    workspace = Workspace.canonicalize((username, wname))
    data_repository = BaseDataRepository.get_one(workspace, name)
    if data_repository is None:
        return ResourceNotFound(resource=name)
    else:
        result, exc = data_repository.move_directory(src_name, dest_name, src_parents, dest_parents)
        if result:
            return make_success_dict(data={'old_path': data['src_path'], 'new_path': data['dest_path']})
        else:
            return InternalFailure(msg=exc.args[0])


@data_repositories_bp.delete('/<name>/folders/<path:path>/')
@data_repositories_bp.delete('/<name>/folders/<path:path>')
@token_auth.login_required
def delete_sub_folder(username, wname, name, path):
    result, error = \
        check_current_user_ownership(username,
                                     f"You cannot create a folder in another user ({username}) repository.")
    if not result:
        return error

    workspace = Workspace.canonicalize((username, wname))
    data_repository = BaseDataRepository.get_one(workspace, name)

    pathlist = path.split('/')
    if len(pathlist) < 1:
        return BadRequestSyntax(msg="Folder path must have at least one item!")

    dir_name = pathlist[-1]
    dir_parents = pathlist[:-1]

    result, exc = data_repository.delete_directory(dir_name, dir_parents)
    if result:
        return make_success_dict()
    else:
        return InternalFailure(msg=exc.args[0])


@data_repositories_bp.patch('/<name>/folders/')
@data_repositories_bp.patch('/<name>/folders')
@token_auth.login_required
def send_files(username, wname, name):
    """
    RequestSyntax:
    {
        <form_of_files>
    }

    ResponseSyntax:
    {
        "created": [
            <file1_name>,
            <file2_name>,
            ...             # for every created file
        ]
    }
    :param username:
    :param wname:
    :param name:
    :return:
    """
    pass


__all__ = [
    'data_repositories_bp',

    'create_data_repository',
    'delete_repo',
    'get_data_repo',
    'get_data_repo_desc',
    'create_sub_folder',
    'move_folder',
    'delete_sub_folder',
    'send_files',
]