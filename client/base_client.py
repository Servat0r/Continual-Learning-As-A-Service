from __future__ import annotations

import zipfile
from typing import Any, Callable

import requests
from http import HTTPStatus
import json
from functools import wraps

from .utils import *


def check_in_session(*params: str):
    def checker(f: Callable):
        @wraps(f)
        def new_method(*args, **kwargs):
            nonlocal params
            self = args[0] if len(args) > 0 else kwargs.get('self')
            if self is None:
                raise RuntimeError("'self' parameter is not given!")
            elif not isinstance(self, BaseClient):
                raise TypeError("'self' parameter is not a client!")
            elif not self.in_session:
                raise RuntimeError("Client is not in an active session!")
            elif not all(self.get_session_data(param) is not None for param in params):
                raise RuntimeError("One or more session parameters are not set!")
            else:
                return f(*args, **kwargs)
        return new_method
    return checker


class _SessionContextManager:

    def __init__(self, cl: BaseClient, username: str, workspace: str, **other_session_data):
        self.client = cl
        self.username = username
        self.workspace = workspace
        self.other_session_data = other_session_data

    def __enter__(self):
        self.client.start_session(self.username, self.workspace, **self.other_session_data)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None or exc_val is not None:
            exc_type = '' if exc_type is None else exc_type
            print(f"Client session got an unexpected uncaught exception ({exc_type}):\n{exc_val}\n{exc_tb}.")
        self.client.end_session()


class BaseClient:

    AUTH = "auth"
    BENCHMARKS = "benchmarks"
    CRITERIONS = "criterions"
    DATA = "data"

    EXPERIMENTS = "experiments"

    METRICSETS = "metricsets"
    MODELS = "models"
    OPTIMIZERS = "optimizers"
    STRATEGIES = "strategies"

    USERS = "users"
    WORKSPACES = "workspaces"

    def __init__(
        self,
        host: str = 'localhost',
        port: int = 5000,
        scheme: str = 'http',
        verbose: bool = False,
    ):
        self.scheme = scheme
        self.host = host
        self.port = port
        self.verbose = verbose

        self._init_session_data()
        self.in_session = False

    @property
    def base_url(self):
        return f"{self.scheme}://{self.host}:{self.port}"

    @property
    def auth(self):
        return BearerAuth(self.auth_token)

    @property
    def auth_base(self):
        return f'{self.base_url}/{self.AUTH}'

    @property
    def users_base(self):
        return f'{self.base_url}/{self.USERS}'

    @property
    def workspaces_base(self):
        return f'{self.users_base}/{self.username}/{self.WORKSPACES}'

    @property
    def data_repositories_base(self):
        return f'{self.workspaces_base}/{self.workspace}/{self.DATA}'

    @property
    def benchmarks_base(self):
        return f"{self.workspaces_base}/{self.workspace}/{self.BENCHMARKS}"

    @property
    def metricsets_base(self):
        return f"{self.workspaces_base}/{self.workspace}/{self.METRICSETS}"

    @property
    def models_base(self):
        return f"{self.workspaces_base}/{self.workspace}/{self.MODELS}"

    @property
    def optimizers_base(self):
        return f"{self.workspaces_base}/{self.workspace}/{self.OPTIMIZERS}"
    
    @property
    def criterions_base(self):
        return f"{self.workspaces_base}/{self.workspace}/{self.CRITERIONS}"
    
    @property
    def strategies_base(self):
        return f"{self.workspaces_base}/{self.workspace}/{self.STRATEGIES}"

    @property
    def experiments_base(self):
        return f"{self.workspaces_base}/{self.workspace}/{self.EXPERIMENTS}"
    
    @staticmethod
    def get_url(*args):
        return '/'.join(args) + '/'

    # Sessions
    # Context Manager
    def session(self, username: str, workspace: str, **other_session_data):
        return _SessionContextManager(self, username, workspace, **other_session_data)

    def get_session_data(self, name: str):
        return self.current_session_data.get(name)

    def set_session_data(self, name: str, val):
        self.current_session_data[name] = val

    def _init_session_data(self):
        self.current_session_data = {
            'auth_token': None,
            'username': None,
            'workspace': None,
        }
        self.in_session = False

    def start_session(self, username: str, workspace: str = None, **other_session_data) -> bool:
        if not self.in_session:
            self.set_user(username)
            self.set_workspace(workspace)
            for name, value in other_session_data:
                self.set_session_data(name, value)
            self.in_session = True
            return True
        else:
            return False

    def end_session(self) -> bool:
        if self.in_session:
            self._init_session_data()
            return True
        else:
            return False

    # Common properties
    @property
    def username(self):
        return self.current_session_data.get('username')

    @property
    def workspace(self):
        return self.current_session_data.get('workspace')

    @property
    def auth_token(self):
        return self.current_session_data.get('auth_token')

    def set_user(self, username: str):
        self.set_session_data('username', username)

    def set_workspace(self, workspace: str):
        self.set_session_data('workspace', workspace)

    # "Customized" client HTTP requests
    def request(
            self, method: str, url_items: str | list[str], data=None,
            auth=True, headers=None, params=None, files=None,
    ):
        if isinstance(url_items, str):
            url = url_items
        elif isinstance(url_items, list):
            url = self.get_url(*url_items)
        else:
            raise TypeError()
        if self.verbose:
            print(f"Sending request ({method} @ {url}) ...")
        return requests.request(
            method, url, params=params,
            files=files, json=data, headers=headers,
            auth=(self.auth if auth else None),
        )

    def get(self, url_items: str | list[str], data=None, auth=True, headers=None, params=None, files=None):
        return self.request('get', url_items, data=data, auth=auth, headers=headers, params=params, files=files)

    def post(self, url_items: str | list[str], data=None, auth=True, headers=None, params=None, files=None):
        return self.request('post', url_items, data=data, auth=auth, headers=headers, params=params, files=files)

    def put(self, url_items: str | list[str], data=None, auth=True, headers=None, params=None, files=None):
        return self.request('put', url_items, data=data, auth=auth, headers=headers, params=params, files=files)

    def patch(self, url_items: str | list[str], data=None, auth=True, headers=None, params=None, files=None):
        return self.request('patch', url_items, data=data, auth=auth, headers=headers, params=params, files=files)

    def delete(self, url_items: str | list[str], data=None, auth=True, headers=None, params=None, files=None):
        return self.request('delete', url_items, data=data, auth=auth, headers=headers, params=params, files=files)

    def head(self, url_items: str | list[str], data=None, auth=True, headers=None, params=None, files=None):
        return self.request('head', url_items, data=data, auth=auth, headers=headers, params=params, files=files)

    def options(self, url_items: str | list[str], data=None, auth=True, headers=None, params=None, files=None):
        return self.request('options', url_items, data=data, auth=auth, headers=headers, params=params, files=files)

    # API Requests
    def register(self, username: str, email: str, password: str):
        data = {
            'username': username,
            'email': email,
            'password': password,
        }
        url = self.get_url(self.users_base)
        resp = self.post(url, data, auth=False)
        return resp  # resp.status_code, resp.headers, resp.json()

    @check_in_session()
    def login(self, username: str, password: str):
        url = self.get_url(self.auth_base, 'login')
        data = {
            'username': username,
            'password': password,
        }

        response = self.post(url, data, auth=False)
        data = response.json()

        if response.status_code == HTTPStatus.OK:
            self.set_session_data('auth_token', data.pop('token'))
        return response

    @check_in_session('auth_token')
    def logout(self, exit_session=True):
        url = self.get_url(self.auth_base, 'logout')
        response = self.post(url)

        if response.status_code == HTTPStatus.OK and exit_session:
            self.end_session()
        return response

    @check_in_session('auth_token')
    def get_user(self, username: str = None):
        if username is None:
            username = self.username
        return self.get([self.users_base, username])

    @check_in_session('auth_token', 'username')
    def edit_user(self, new_username, new_email):
        if (new_username is None) or (new_email is None):
            raise TypeError('New username and email cannot be None!')
        else:
            data = {
                'username': new_username,
                'email': new_email,
            }
            url = self.get_url(self.users_base, self.username)
            return self.patch(url, data)

    @check_in_session('auth_token', 'username')
    def edit_password(self, old_password, new_password):
        if (old_password is None) or (new_password is None):
            raise TypeError('Old and new passwords cannot be None!')
        else:
            data = {
                'old_password': old_password,
                'new_password': new_password,
            }
            return self.patch([self.users_base, self.username, 'password'], data)

    @check_in_session('auth_token', 'username')
    def delete_user(self):
        return self.delete([self.users_base, self.username])

    @check_in_session('auth_token', 'username')
    def create_workspace(self, workspace_name: str):
        data = {
            "name": workspace_name,
        }
        resp = self.post([self.workspaces_base], data)
        if resp.status_code == HTTPStatus.CREATED:
            self.set_workspace(workspace_name)
        return resp

    @check_in_session('auth_token', 'username', 'workspace')
    def get_workspace(self, workspace_name: str = None):
        if workspace_name is None:
            if self.workspace is None:
                raise ValueError("Unknown workspace name")
            else:
                workspace_name = self.workspace
        return self.get([self.workspaces_base, workspace_name])

    @check_in_session('auth_token', 'username', 'workspace')
    def open_workspace(self, workspace_name: str = None):
        if workspace_name is None:
            if self.workspace is None:
                raise ValueError("Unknown workspace name")
            else:
                workspace_name = self.workspace
        return self.patch([self.workspaces_base, workspace_name, 'status'], data={'status': 'OPEN'})

    @check_in_session('auth_token', 'username', 'workspace')
    def close_workspace(self, workspace_name: str = None):
        if workspace_name is None:
            if self.workspace is None:
                raise ValueError("Unknown workspace name")
            else:
                workspace_name = self.workspace
        return self.patch([self.workspaces_base, workspace_name, 'status'], data={'status': 'CLOSED'})

    @check_in_session('auth_token', 'username', 'workspace')
    def delete_workspace(self, workspace_name: str = None):
        if workspace_name is None:
            if self.workspace is None:
                raise ValueError("Unknown workspace name")
            else:
                workspace_name = self.workspace
        return self.delete([self.workspaces_base, workspace_name])

    # Data Repositories
    @check_in_session('auth_token', 'username', 'workspace')
    def create_data_repository(self, repo_name: str, repo_desc: str = None):
        if repo_name is None:
            raise ValueError("Repository name cannot be None.")
        else:
            return self.post([self.data_repositories_base], data={'name': repo_name, 'description': repo_desc})

    @check_in_session('auth_token', 'username', 'workspace')
    def get_data_repository(self, repo_name: str):
        if repo_name is None:
            raise ValueError("Repository name cannot be None.")
        else:
            return self.get([self.data_repositories_base, repo_name])

    @check_in_session('auth_token', 'username', 'workspace')
    def get_data_repository_desc(self, repo_name: str):
        if repo_name is None:
            raise ValueError("Repository name cannot be None.")
        else:
            return self.get([self.data_repositories_base, repo_name, 'desc'])

    @check_in_session('auth_token', 'username', 'workspace')
    def delete_data_repository(self, repo_name: str):
        if repo_name is None:
            raise ValueError("Repository name cannot be None.")
        else:
            return self.delete([self.data_repositories_base, repo_name])

    @check_in_session('auth_token', 'username', 'workspace')
    def create_subdir(self, repo_name: str, folder_name: str, folder_path: list[str] = None):
        if repo_name is None:
            raise ValueError("Repository name cannot be None.")
        folder_path = [] if folder_path is None else folder_path
        data = {
            'name': folder_name,
            'path': '/'.join(folder_path),
        }
        return self.post([self.data_repositories_base, repo_name, 'folders'], data=data)

    @check_in_session('auth_token', 'username', 'workspace')
    def move_subdir(self, repo_name: str, src_path: str, dest_path: str):
        if repo_name is None:
            raise ValueError("Repository name cannot be None.")
        data = {
            'src_path': src_path,
            'dest_path': dest_path,
        }
        return self.patch([self.data_repositories_base, repo_name, 'folders'], data=data)

    @check_in_session('auth_token', 'username', 'workspace')
    def delete_subdir(self, repo_name: str, path: str):
        if repo_name is None:
            raise ValueError("Repository name cannot be None.")
        return self.delete([self.data_repositories_base, repo_name, 'folders', path])

    @check_in_session('auth_token', 'username', 'workspace')
    def send_files(
            self,
            repo_name: str,
            files_and_labels: list[tuple[str, str, int]],   # source_path, dest_path, label
            base_path: list[str],
            files_mode='plain',  # file transfer mode: either 'plain' (plain files) or 'zip' (a zip file to extract)
            zip_file_name='files.zip',
    ):
        translated: list = []     # files, labels, (mode)
        info: dict = {
            'labels': {},
            'modes': {
                'files': files_mode,
            }
        }
        if files_mode == 'plain':
            for src_path, dest_path, label in files_and_labels:
                dest_path = dest_path.replace('\\', '/')    # for uniforming unix and windows paths
                label = str(label)
                translated.append(('files', (dest_path, open(src_path, 'rb'))))
                info['labels'][dest_path] = label
                translated.append(('info', ('info', json.dumps(info))))
                """
                translated: list[tuple[str, tuple[str, Any]]] = [
                    (str(label), (dest_path.replace('\\', '/'), open(src_path, 'rb')))
                    for src_path, dest_path, label in files_and_labels
                ]
                """
                return self.patch(
                    [self.data_repositories_base, repo_name, 'folders', 'files'] + base_path,
                    files=translated, data=info,
                )
        elif files_mode == 'zip':
            with zipfile.ZipFile(zip_file_name, 'w') as zipf:
                for src_path, dest_path, label in files_and_labels:
                    dest_path = dest_path.replace('\\', '/')  # for uniforming unix and windows paths
                    label = str(label)
                    zipf.write(filename=src_path, arcname=dest_path)
                    info['labels'][dest_path] = label

            with open(zip_file_name, 'rb') as zipf:
                translated.append(('files', ('files', zipf)))
                translated.append(('info', ('info', json.dumps(info))))
                return self.patch(
                    [self.data_repositories_base, repo_name, 'folders', 'files'] + base_path,
                    files=translated, data=info,
                )
        else:
            raise ValueError(f"Files transfer mode '{files_mode}' is unknown or not implemented.")

    # Benchmarks
    @check_in_session('auth_token', 'username', 'workspace')
    def create_benchmark(self, name: str, build_config_data: dict, description: str = None):
        data = {
            'name': name,
            'build': build_config_data,
        }
        if description is not None:
            data['description'] = description
        return self.post(self.benchmarks_base, data=data)

    @check_in_session('auth_token', 'username', 'workspace')
    def get_benchmark(self, name: str):
        return self.get([self.benchmarks_base, name])

    @check_in_session('auth_token', 'username', 'workspace')
    def rename_benchmark(self, name: str, new_name: str):
        return self.update_benchmark(name, {'name': new_name})

    @check_in_session('auth_token', 'username', 'workspace')
    def update_benchmark(self, name: str, updata: dict):
        return self.patch([self.benchmarks_base, name], data=updata)

    @check_in_session('auth_token', 'username', 'workspace')
    def delete_benchmark(self, name: str):
        return self.delete([self.benchmarks_base, name])

    # MetricSets
    @check_in_session('auth_token', 'username', 'workspace')
    def create_metric_set(self, name: str, build_config_data: dict, description: str = None):
        data = {
            'name': name,
            'build': build_config_data,
        }
        if description is not None:
            data['description'] = description
        return self.post(self.metricsets_base, data=data)

    @check_in_session('auth_token', 'username', 'workspace')
    def get_metricset(self, name: str):
        return self.get([self.metricsets_base, name])

    @check_in_session('auth_token', 'username', 'workspace')
    def rename_metric_set(self, name: str, new_name: str):
        return self.update_metric_set(name, {'name': new_name})

    @check_in_session('auth_token', 'username', 'workspace')
    def update_metric_set(self, name: str, updata: dict):
        return self.patch([self.metricsets_base, name], data=updata)

    @check_in_session('auth_token', 'username', 'workspace')
    def delete_metric_set(self, name: str):
        return self.delete([self.metricsets_base, name])

    # Models
    @check_in_session('auth_token', 'username', 'workspace')
    def create_model(self, name: str, build_config_data: dict, description: str = None):
        data = {
            'name': name,
            'build': build_config_data,
        }
        if description is not None:
            data['description'] = description
        return self.post(self.models_base, data=data)

    @check_in_session('auth_token', 'username', 'workspace')
    def get_model(self, name: str):
        return self.get([self.models_base, name])

    @check_in_session('auth_token', 'username', 'workspace')
    def rename_model(self, name: str, new_name: str):
        return self.update_model(name, {'name': new_name})

    @check_in_session('auth_token', 'username', 'workspace')
    def update_model(self, name: str, updata: dict):
        return self.patch([self.models_base, name], data=updata)

    @check_in_session('auth_token', 'username', 'workspace')
    def delete_model(self, name: str):
        return self.delete([self.models_base, name])

    # Optimizer
    @check_in_session('auth_token', 'username', 'workspace')
    def create_optimizer(self, name: str, build_config_data: dict, description: str = None):
        data = {
            'name': name,
            'build': build_config_data,
        }
        if description is not None:
            data['description'] = description
        return self.post(self.optimizers_base, data=data)

    @check_in_session('auth_token', 'username', 'workspace')
    def get_optimizer(self, name: str):
        return self.get([self.optimizers_base, name])

    @check_in_session('auth_token', 'username', 'workspace')
    def rename_optimizer(self, name: str, new_name: str):
        return self.update_optimizer(name, {'name': new_name})

    @check_in_session('auth_token', 'username', 'workspace')
    def update_optimizer(self, name: str, updata: dict):
        return self.patch([self.optimizers_base, name], data=updata)

    @check_in_session('auth_token', 'username', 'workspace')
    def delete_optimizer(self, name: str):
        return self.delete([self.optimizers_base, name])

    # Criterions
    @check_in_session('auth_token', 'username', 'workspace')
    def create_criterion(self, name: str, build_config_data: dict, description: str = None):
        data = {
            'name': name,
            'build': build_config_data,
        }
        if description is not None:
            data['description'] = description
        return self.post(self.criterions_base, data=data)

    @check_in_session('auth_token', 'username', 'workspace')
    def get_criterion(self, name: str):
        return self.get([self.criterions_base, name])

    @check_in_session('auth_token', 'username', 'workspace')
    def rename_criterion(self, name: str, new_name: str):
        return self.update_criterion(name, {'name': new_name})

    @check_in_session('auth_token', 'username', 'workspace')
    def update_criterion(self, name: str, updata: dict):
        return self.patch([self.criterions_base, name], data=updata)

    @check_in_session('auth_token', 'username', 'workspace')
    def delete_criterion(self, name: str):
        return self.delete([self.criterions_base, name])

    # Strategies
    @check_in_session('auth_token', 'username', 'workspace')
    def create_strategy(self, name: str, build_config_data: dict, description: str = None):
        data = {
            'name': name,
            'build': build_config_data,
        }
        if description is not None:
            data['description'] = description
        return self.post(self.strategies_base, data=data)

    @check_in_session('auth_token', 'username', 'workspace')
    def get_strategy(self, name: str):
        return self.get([self.strategies_base, name])

    @check_in_session('auth_token', 'username', 'workspace')
    def rename_strategy(self, name: str, new_name: str):
        return self.update_strategy(name, {'name': new_name})

    @check_in_session('auth_token', 'username', 'workspace')
    def update_strategy(self, name: str, updata: dict):
        return self.patch([self.strategies_base, name], data=updata)

    @check_in_session('auth_token', 'username', 'workspace')
    def delete_strategy(self, name: str):
        return self.delete([self.strategies_base, name])

    # Experiments
    @check_in_session('auth_token', 'username', 'workspace')
    def create_experiment(self, name: str, build_config_data: dict, description: str = None):
        data = {
            'name': name,
            'build': build_config_data,
        }
        if description is not None:
            data['description'] = description
        return self.post(self.experiments_base, data=data)

    @check_in_session('auth_token', 'username', 'workspace')
    def setup_experiment(self, name: str):
        return self.patch([self.experiments_base, name, 'setup'])

    @check_in_session('auth_token', 'username', 'workspace')
    def start_experiment(self, name: str):
        return self.patch([self.experiments_base, name], data={'status': 'START'})

    @check_in_session('auth_token', 'username', 'workspace')
    def get_experiment_status(self, name: str):
        return self.get([self.experiments_base, name, 'status'])

    @check_in_session('auth_token', 'username', 'workspace')
    def get_experiment_results(self, name: str):
        return self.get([self.experiments_base, name, 'results', 'exec'])

    @check_in_session('auth_token', 'username', 'workspace')
    def get_experiment_settings(self, name: str):
        return self.get([self.experiments_base, name, 'settings'])

    @check_in_session('auth_token', 'username', 'workspace')
    def get_experiment_model(self, name: str):
        return self.get([self.experiments_base, name, 'model'])

    @check_in_session('auth_token', 'username', 'workspace')
    def get_experiment_csv_results(self, name: str):
        return self.get([self.experiments_base, name, 'results', 'csv'])

    @check_in_session('auth_token', 'username', 'workspace')
    def delete_experiment(self, name: str):
        return self.delete([self.experiments_base, name])


__all__ = [
    'check_in_session',
    'BaseClient',
]