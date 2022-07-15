from __future__ import annotations

import json
from http import HTTPStatus
from flask import Blueprint, request

from application.errors import *
from application.utils import *
from application.validation import *
from application.data_managing import TFContent
from application.models import Workspace

from .auth import *
from application.data_managing import BaseDataRepository


data_repositories_bp = Blueprint('data_repositories', __name__,
                                 url_prefix='/users/<user:username>/workspaces/<workspace:wname>/data')


@linker.args_rule('DataRepository')
def data_repository_args(repository: BaseDataRepository):
    username = repository.get_owner().get_name()
    wname = repository.get_workspace().get_name()
    name = repository.get_name()
    return {
        'username': username,
        'wname': wname,
        'name': name,
    }


@data_repositories_bp.post('/')
@data_repositories_bp.post('')
@token_auth.login_required
@check_json(False, required={'name'}, optionals={'description'})
@check_ownership(msg="You cannot create a data repository for another user ({user}).", eval_args={'user': 'username'})
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
    data, opts, extras = get_check_json_data()
    workspace = Workspace.canonicalize((username, wname))
    name = data['name']
    description = data.get('description')
    result, msg = validate_workspace_resource_experiment(name)
    if not result:
        return InvalidResourceName(msg)
    data_repository = BaseDataRepository.create(name, workspace, desc=description)
    if data_repository is not None:
        data = linker.make_links(data_repository.to_dict())
        return make_success_dict(HTTPStatus.CREATED, data=data)
    else:
        return InternalFailure(msg=f"Failed to create data repository '{name}'.")


@data_repositories_bp.delete('/<resource:name>/')
@data_repositories_bp.delete('/<resource:name>')
@token_auth.login_required
@check_ownership(msg="You cannot delete another user ('{user}') data repository.", eval_args={'user': 'username'})
def delete_repo(username, wname, name):

    try:
        current_user = token_auth.current_user()
        workspace = Workspace.canonicalize((current_user, wname))
        data_repository = BaseDataRepository.get_one(workspace, name)
        if data_repository is not None:
            result, exc = data_repository.delete()
            if result:
                return make_success_dict(msg=f"Data repository '{name}' successfully deleted.")
            else:
                return InternalFailure(msg=exc.args[0], exception=str(exc))
        else:
            return ResourceNotFound(resource=name)
    except Exception as ex:
        print(ex, ex.args)
        return InternalFailure(exception=str(ex))


@data_repositories_bp.get('/<resource:name>/')
@data_repositories_bp.get('/<resource:name>')
@token_auth.login_required
@linker.link_rule('DataRepository', blueprint=data_repositories_bp)
@check_ownership(msg="You cannot retrieve another user ({user}) data repository.", eval_args={'user': 'username'})
def get_data_repo(username, wname, name):
    current_user = token_auth.current_user()
    workspace = Workspace.canonicalize((current_user, wname))
    data_repository = BaseDataRepository.get_one(workspace, name)
    if data_repository is not None:
        data = linker.make_links(data_repository.to_dict())
        return make_success_dict(data=data)
    else:
        return ResourceNotFound(resource=name)


@data_repositories_bp.get('/<resource:name>/desc/')
@data_repositories_bp.get('/<resource:name>/desc')
@token_auth.login_required
@check_ownership(msg="You cannot retrieve another user ({user}) data repository.", eval_args={'user': 'username'})
def get_data_repo_desc(username, wname, name):
    current_user = token_auth.current_user()
    workspace = Workspace.canonicalize((current_user, wname))
    data_repository = BaseDataRepository.get_one(workspace, name)
    if data_repository is not None:
        desc = data_repository.get_description()
        return make_success_dict(data={'description': desc})
    else:
        return ResourceNotFound(resource=name)


@data_repositories_bp.post('/<resource:name>/folders/')
@data_repositories_bp.post('/<resource:name>/folders')
@token_auth.login_required
@check_json(False, required={'name'}, optionals={'path'})
@check_ownership("You cannot create a directory in another user ({user}) data repository", eval_args={'user': 'username'})
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
    data, opts, extras = get_check_json_data()
    folder_name = data['name']
    folder_path = data.get('path')

    result, msg = validate_workspace_resource_experiment(folder_name)
    if not result:
        return InvalidResourceName(msg)

    result, msg = validate_path(folder_path)
    if not result:
        return InvalidPath(msg)

    if (folder_path is not None) and not isinstance(folder_path, str):
        return BadRequestSyntax(msg=f"'folder_path' must be a string!")

    folders = folder_path.split('/') if folder_path is not None else None

    folders = [val for val in folders if len(val) > 0]

    workspace = Workspace.canonicalize((username, wname))
    data_repository = BaseDataRepository.get_one(workspace, name)
    if data_repository is not None:
        result, exc = data_repository.add_directory(folder_name, folders)
        if result:
            return make_success_dict(HTTPStatus.CREATED)
        else:
            return InternalFailure(msg=exc.args[0])
    else:
        return ResourceNotFound(resource=name)


@data_repositories_bp.patch('/<resource:name>/folders/')
@data_repositories_bp.patch('/<resource:name>/folders')
@token_auth.login_required
@check_json(False, required={'src_path', 'dest_path'})
@check_ownership("You cannot create a folder in another user ({user}) repository.", eval_args={'user': 'username'})
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
    result, error = check_current_user_ownership(
        username,
        f"You cannot create a folder in another user ({username}) repository.",
    )
    if not result:
        return error

    data, opts, extras = get_check_json_data()
    src_path_str = data['src_path']
    dest_path_str = data['dest_path']
    
    result, msg = validate_path(src_path_str)
    if not result:
        return InvalidPath(msg)

    result, msg = validate_path(dest_path_str)
    if not result:
        return InvalidPath(msg)

    src_path = src_path_str.split('/')
    src_path = [item for item in src_path if len(item) > 0]

    dest_path = dest_path_str.split('/')
    dest_path = [item for item in dest_path if len(item) > 0]


    if len(src_path) < 1 or len(dest_path) < 1:
        return BadRequestSyntax(msg="Source and destination paths must have at least one item!")

    src_parents = src_path[:-1]
    dest_parents = dest_path[:-1]
    src_name = src_path[-1]
    dest_name = dest_path[-1]

    workspace = Workspace.canonicalize((username, wname))
    data_repository = BaseDataRepository.get_one(workspace, name)
    if data_repository is not None:
        result, exc = data_repository.move_directory(src_name, dest_name, src_parents, dest_parents)
        if result:
            return make_success_dict(data={'old_path': data['src_path'], 'new_path': data['dest_path']})
        else:
            return InternalFailure(msg=exc.args[0])
    else:
        return ResourceNotFound(resource=name)


@data_repositories_bp.delete('/<resource:name>/folders/<path:path>/')
@data_repositories_bp.delete('/<resource:name>/folders/<path:path>')
@token_auth.login_required
@check_ownership("You cannot delete a folder in another user ({user}) repository.", eval_args={'user': 'username'})
def delete_sub_folder(username, wname, name, path):
    result, error = \
        check_current_user_ownership(username,
                                     f"You cannot create a folder in another user ({username}) repository.")
    if not result:
        return error

    result, msg = validate_path(path)
    if not result:
        return InvalidPath(msg)

    workspace = Workspace.canonicalize((username, wname))
    data_repository = BaseDataRepository.get_one(workspace, name)

    pathlist = path.split('/')
    pathlist = [item for item in pathlist if len(item) > 0]
    if len(pathlist) < 1:
        return BadRequestSyntax(msg="Folder path must have at least one item!")

    dir_name = pathlist[-1]
    dir_parents = pathlist[:-1]

    result, exc = data_repository.delete_directory(dir_name, dir_parents)
    if result:
        return make_success_dict()
    else:
        return InternalFailure(msg=exc.args[0])


# Fa anche da update dei files
@data_repositories_bp.patch('/<resource:name>/folders/files/<path:path>/')
@data_repositories_bp.patch('/<resource:name>/folders/files/<path:path>')
@token_auth.login_required
@check_ownership("You cannot send files to another user ({user}) repository.", eval_args={'user': 'username'})
def send_files(username, wname, name, path):
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
    :param path:
    :return:
    """
    result, error = check_current_user_ownership(
        username,
        f"You cannot create a folder in another user ({username}) repository.",
    )
    if not result:
        return error

    workspace = Workspace.canonicalize((username, wname))
    data_repository = BaseDataRepository.get_one(workspace, name)

    result, msg = validate_path(path)
    if not result:
        return InvalidPath(msg)

    base_path_list: list[str] = path.split('/')
    base_path_list = [item for item in base_path_list if len(item) > 0]

    filestores = request.files
    data = {'success': [], 'n_success': 0}
    total = 0
    if len(filestores) < 1:
        return MissingFile()
    else:
        files = filestores.getlist('files')
        info = json.load(filestores.getlist('info')[0].stream)
        modes = info['modes']  # json.load(filestores.getlist('modes')[0].stream)
        files_and_labels: list[TFContent] = []
        files_mode = modes.get('files', 'plain')

        if files_mode == 'plain':
            for fstorage in files:
                file_path = fstorage.filename
                result, msg = validate_path(file_path)
                if not result:
                    return InvalidPath(msg)
                pathlist = file_path.split('/')
                pathlist = [item for item in pathlist if len(item) > 0]

                dir_path_list = base_path_list + pathlist[:-1]
                file_name = pathlist[-1]
                files_and_labels.append((file_name, dir_path_list, fstorage))
            successes = data_repository.add_files(files_and_labels)
            data['success'] += successes
            data['n_success'] += len(successes)

        elif files_mode == 'zip':
            for fstorage in files:  # zip file
                total, successes = data_repository.add_archive(fstorage, base_path_list)
                data['success'] += successes
                data['n_success'] += len(successes)
        else:
            return InternalFailure(msg=f"File transfer mode '{files_mode}' is unknown or not implemented.")

        if data['n_success'] >= total:
            return make_success_dict(data=data)
        else:
            return InternalFailure(msg="At least one file has not correctly been updated.", payload=data)


@data_repositories_bp.patch('/<resource:name>/')
@data_repositories_bp.patch('/<resource:name>')
@token_auth.login_required
@check_json(False, optionals={'name', 'description'})
@check_ownership("You cannot update another user ({user}) repository.", eval_args={'user': 'username'})
def update_data_repository(username, wname, name):
    """
    Updates data repository (name or description).
    :param username:
    :param wname:
    :param name:
    :return:
    """
    data, opts, extras = get_check_json_data()
    current_user = token_auth.current_user()
    workspace = Workspace.canonicalize((current_user, wname))
    data_repository = BaseDataRepository.get_one(workspace, name)
    if data_repository is not None:
        result, msg = data_repository.update(data)
        return make_success_dict() if result else InternalFailure(payload={'error': msg})
    else:
        return ResourceNotFound(resource=name)


@data_repositories_bp.get('/<resource:name>/folders/<path:path>/')
@data_repositories_bp.get('/<resource:name>/folders/<path:path>')
@token_auth.login_required
@check_ownership("You cannot retrieve another user ({user}) repository folder content.", eval_args={'user': 'username'})
def get_folder_content(username, wname, name, path):
    current_user = token_auth.current_user()
    workspace = Workspace.canonicalize((current_user, wname))
    data_repository = BaseDataRepository.get_one(workspace, name)
    if data_repository is not None:
        files = data_repository.get_all_files(path)
        num_files = len(files) if files is not None else 0
        return make_success_dict(data={'num_files': num_files, 'files': files})
    else:
        return ResourceNotFound(resource=name)


@data_repositories_bp.patch('/<resource:name>/folders/rename/<path:path>/')
@data_repositories_bp.patch('/<resource:name>/folders/rename/<path:path>')
@token_auth.login_required
@check_json(False, optionals={'new_name'})
@check_ownership("You cannot rename another user ({user}) repository folder.", eval_args={'user': 'username'})
def rename_folder(username, wname, name, path):
    data, opts, extras = get_check_json_data()
    new_name = data.get('new_name')
    if new_name is None:
        return make_success_dict(status=HTTPStatus.NOT_MODIFIED)
    current_user = token_auth.current_user()
    workspace = Workspace.canonicalize((current_user, wname))
    data_repository = BaseDataRepository.get_one(workspace, name)
    if data_repository is not None:
        result, exc = data_repository.rename_directory(path, new_name)
        return make_success_dict() if result else InternalFailure(
            payload={'error': str(exc), 'error_msg': str(exc.args)}
        )
    else:
        return ResourceNotFound(resource=name)


@data_repositories_bp.delete('/<resource:name>/folders/files/')
@data_repositories_bp.delete('/<resource:name>/folders/files')
@token_auth.login_required
@check_json(False, required={'files'})
@check_ownership("You cannot delete another user ({user}) repository files.", eval_args={'user': 'username'})
def delete_files(username, wname, name):
    """
    Request Syntax:
    {
        "files": [
            <first_file_path>,
            <second_file_path>,
            ...
        ]
    }
    :param username:
    :param wname:
    :param name:
    :return:
    """
    data, opts, extras = get_check_json_data()
    files = data.get('files')
    if files is None:
        return InternalFailure()
    f_name_dirs = []
    for file in files:
        file = file.split('/')
        file = [s for s in file if len(s) > 0]
        f_name_dirs += [(file[-1], file[:-1])]
    current_user = token_auth.current_user()
    workspace = Workspace.canonicalize((current_user, wname))
    data_repository = BaseDataRepository.get_one(workspace, name)
    if data_repository is not None:
        deleted = data_repository.delete_files(f_name_dirs, locked=False, parents_locked=False)
        n_deleted = len(deleted)
        payload = {'n_deleted': n_deleted, 'deleted': deleted}
        if n_deleted >= len(files):
            return make_success_dict(data=payload)
        else:
            return InternalFailure(msg="At least one file has not correctly been deleted.", payload=payload)
    else:
        return ResourceNotFound(resource=name)


__all__ = [
    'data_repositories_bp',

    'create_data_repository',
    'get_data_repo',
    'get_data_repo_desc',
    'update_data_repository',
    'delete_repo',

    'create_sub_folder',
    'get_folder_content',
    'move_folder',
    'rename_folder',
    'delete_sub_folder',

    'send_files',
    'delete_files',
]