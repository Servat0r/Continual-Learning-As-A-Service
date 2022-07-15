"""
Common constants.
"""
from __future__ import annotations

import sys
import traceback
import typing as t
import os
import schema as sch
from abc import ABC, abstractmethod
from datetime import datetime
from functools import wraps

import torch
from torch.nn.modules import Module
from http import HTTPStatus
from flask import Flask, Blueprint, url_for, Request, jsonify, Response, request, g
from werkzeug.exceptions import BadRequest
from flask_executor import Executor

from .errors import *

# Executor
executor = Executor()

# TypeVars
TBoolStr = t.TypeVar('TBoolStr', bound=tuple[bool, t.Optional[str]])
TBoolExc = t.TypeVar('TBoolExc', bound=tuple[bool, t.Optional[Exception]])
TBoolAny = t.TypeVar('TBoolAny', bound=tuple[bool, t.Any])
TOptBoolAny = t.TypeVar('TOptBoolAny', bound=tuple[t.Optional[bool], t.Any])
TDesc = t.TypeVar('TDesc', bound=dict[str, t.Any])

# Classic methods
GET = 'GET'
POST = 'POST'
PUT = 'PUT'
PATCH = 'PATCH'
HEAD = 'HEAD'
OPTIONS = 'OPTIONS'
DELETE = 'DELETE'

# Default success and error messages
_DFL_SUCCESS_MSG = 'Request successfully completed.'


def make_success_kwargs(status: int = HTTPStatus.OK, msg: str = _DFL_SUCCESS_MSG, **kwargs) -> Response:
    """
    Default success responses maker.
    :param status: HTTP success status code.
    :param msg: Descriptive message.
    :param kwargs: Extra arguments.
    :return: A Response object.
    """
    err_dict = kwargs if kwargs is not None else {}
    err_dict['message'] = msg

    response = jsonify(err_dict)
    response.status = status
    return response


def make_success_dict(status: int = HTTPStatus.OK, msg: str = _DFL_SUCCESS_MSG, data: dict = None) -> Response:
    if data is None:
        data = {}
    data['message'] = msg

    response = jsonify(data)
    response.status = status
    return response


# JSON checking!
def checked_json(request: Request, keyargs: bool = False, required: set[str] = None, optionals: set[str] = None,
                 force: bool = True) -> tuple[t.Any | None, ServerResponseError | None, list[str], list[str]]:
    """
    Checks if request data is JSON-syntactically correct and has exactly the expected parameters (even optional ones).
    :param request: Current incoming request.
    :param keyargs: If true, enables optional parameters in the request.
    :param required: Required parameters for this request.
    :param optionals: Optional parameters for this request (except for "key" extra arguments).
    :param force: To be passed to request.get_json(...).
    :return: A couple (dict, error), where error is None on success and an error as defined in
    application.errors.handlers on error, and dict is a dictionary that must be interpreted as:
        - on success, request body as JSON;
        - if error is BadJSONSyntax, an empty dictionary to be ignored;
        - if error is MissingParameter, a list of all missing required parameters;
        - if error is InvalidParameter, a list of all unexpected parameters.
    """
    if required is None:
        required = set()

    if optionals is None:
        optionals = set()

    if not required.isdisjoint(optionals):
        raise ValueError("'required' and 'optionals' sets must be disjoint!")

    try:
        data = request.get_json(force=force)
        if data is None:
            return None, BadJSONSyntax, [], []
        else:
            keys = data.keys()
            missing_params = required.copy()
            given_optionals: list[str] = []
            extras: list[str] = []
            opts_bak = optionals.copy()    # (deep copy in this case)

            for param in keys:
                if param in missing_params:
                    missing_params.remove(param)
                elif param in opts_bak:
                    opts_bak.remove(param)
                    given_optionals.append(param)
                else:
                    extras.append(param)

            if len(missing_params) > 0:
                return {'parameter': missing_params}, MissingParameter, given_optionals, extras
            elif (not keyargs) and (len(extras) > 0):
                return {'parameter': extras}, InvalidParameter, given_optionals, extras
            else:
                return data, None, given_optionals, extras
    except BadRequest:
        return None, BadJSONSyntax, [], []


# todo incomplete!
def schema_checked_json(
        keyargs=False, required: set[str] | dict[str, object] = None,
        optionals: set[str] | dict[str, object] = None, force: bool = True,
):
    schema = {}
    if isinstance(required, set):
        required = {item: object for item in required}
    if isinstance(optionals, set):
        optionals = {item: object for item in optionals}
    schema.update(required)
    schema.update({sch.Optional(key): value for key, value in optionals.items()})
    if keyargs:
        schema.update({str: object})
    data = request.get_json(force=force)


def check_json(keyargs=False, required=None, optionals=None, force=True):
    """
    Decorator for automatic checked_json.
    :param keyargs:
    :param required:
    :param optionals:
    :param force:
    :return:
    """
    def wrapper(f: t.Callable):
        @wraps(f)
        def new_f(*args, **kwargs):
            data, error, opts, extras = checked_json(request, keyargs, required, optionals, force)
            if error is not None:
                if data is not None:
                    return error(**data)
                else:
                    return error()
            g.check_json_data = data
            g.check_json_opts = opts
            g.check_json_extras = extras
            return f(*args, **kwargs)
        return new_f
    return wrapper


def get_check_json_data() -> tuple[t.Any | None, list[str], list[str]]:
    data = g.pop('check_json_data', None)
    opts = g.pop('check_json_opts', None)
    extras = g.pop('check_json_extras', None)
    return data, opts, extras


# Linker
class LinkRule:
    def __init__(self, name: str, value: t.Any):
        self.name = name
        self.value = value

    def make_link(self, linker: Linker) -> str:
        link_view_func, link_bp = linker.get_link_rule(self.name)
        args_rule = linker.get_args_rule(self.name)
        if link_view_func is None:
            raise TypeError(f"There is no link rule function registered for '{self.name}'")
        extra_args: TDesc = {}
        if args_rule is not None:
            extra_args.update(args_rule(self.value))
        url = (f"{link_bp.name}." if link_bp is not None else '') + link_view_func.__name__
        return url_for(url, **extra_args)


class Linker:
    @staticmethod
    def default_link_keyword():
        return 'links'

    def __init__(self, app: Flask = None, links_keyword: str = None):
        self.link_rules: dict[str, tuple[t.Callable, t.Optional[Blueprint]]] = {}            # resource_name -> view function .__name__
        self.args_rules: dict[str, t.Callable] = {}     # resource_name -> args for url_for view function
        self.links_keyword = links_keyword
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        if app is None:
            raise ValueError("'app' must be not None")
        if not isinstance(app, Flask):
            raise TypeError("'app' must be an instance of 'Flask'")
        if self.links_keyword is None or len(self.links_keyword) == 0:
            self.links_keyword = app.config.get('LINKS_KEYWORD', self.default_link_keyword())

    def add_link_rule(self, resource_name: str, view_function: t.Callable, blueprint: Blueprint = None, replace=True):
        # resource_name = f"{blueprint.name}.{resource_name}" if resource_name is not None else resource_name
        if not replace:
            old_view = self.link_rules.get(resource_name, None)
            if old_view is not None:
                raise AttributeError(f"A view function was already registered for '{resource_name}'")
        self.link_rules[resource_name] = (view_function, blueprint)

    def add_args_rule(self, resource_name: str, args_function: t.Callable, replace=True):
        # resource_name = f"{blueprint.name}.{resource_name}" if resource_name is not None else resource_name
        if not replace:
            old_args = self.args_rules.get(resource_name, None)
            if old_args is not None:
                raise AttributeError(f"An args function was already registered for '{resource_name}'")
        self.args_rules[resource_name] = args_function

    def get_link_rule(self, name: str) -> tuple[t.Callable, t.Optional[Blueprint]]:
        return self.link_rules.get(name, None)

    def get_args_rule(self, name: str) -> t.Callable:
        return self.args_rules.get(name, None)

    def link_rule(self, resource_name, blueprint: Blueprint = None, replace=True):
        def wrapper(view_function: t.Callable):
            self.add_link_rule(resource_name, view_function, blueprint=blueprint, replace=replace)

            @wraps(view_function)
            def new_view_function(*args, **kwargs):
                return view_function(*args, **kwargs)

            return new_view_function
        return wrapper

    def args_rule(self, resource_name, replace=True):
        def wrapper(view_function: t.Callable):
            self.add_args_rule(resource_name, view_function, replace=replace)

            @wraps(view_function)
            def new_view_function(*args, **kwargs):
                return view_function(*args, **kwargs)

            return new_view_function
        return wrapper

    def _make_links_internal(self, data: t.Any):
        """
        :param data: Either a dict, a sequence, a set or a LinkRule.
        :return:
        """
        if isinstance(data, t.MutableMapping):
            for key, value in data.items():
                data[key] = self._make_links_internal(value)
        elif isinstance(data, t.MutableSequence):
            for i in range(len(data)):
                data[i] = self._make_links_internal(data[i])
        elif isinstance(data, t.MutableSet):
            data = {self._make_links_internal(item) for item in data}
        elif isinstance(data, tuple):
            if len(data) != 2:
                raise TypeError("A tuple link rule must have a length of 2!")
            data = self._make_links_internal(LinkRule(data[0], data[1]))
        elif isinstance(data, LinkRule):
            data = data.make_link(self)
        else:
            raise TypeError(f"Unknown type {type(data).__name__}")
        return data

    def make_links(self, json_data: TDesc) -> TDesc:
        preprocess_links = json_data.pop(self.links_keyword, None)
        if preprocess_links is not None:
            if not isinstance(preprocess_links, dict):
                raise TypeError("Malformed server response for resource linking")
            else:
                links_dict = self._make_links_internal(preprocess_links)
                """
                links_dict: TDesc = {}
                for field_name, field_data in preprocess_links.items():
                    resource_name, resource_val = field_data
                    link_view_func, link_bp = self.get_link_rule(resource_name)
                    args_rule = self.get_args_rule(resource_name)
                    if link_view_func is None:
                        raise TypeError(f"There is no link rule function registered for '{resource_name}'")
                    extra_args: TDesc = {}
                    if args_rule is not None:
                        extra_args.update(args_rule(resource_val))
                    url = (f"{link_bp.name}." if link_bp is not None else '') + link_view_func.__name__
                    resource_url = url_for(url, **extra_args)
                    links_dict[field_name] = resource_url
                """
                json_metadata = json_data.get('metadata', None)
                if json_metadata is None:
                    json_metadata = {}
                    json_data['metadata'] = json_metadata
                json_metadata['links'] = links_dict
        return json_data

    def make_decor_links(self, view_function: t.Callable):
        @wraps(view_function)
        def new_view_function(*args, **kwargs):
            response: Response = view_function(*args, **kwargs)
            json_data = response.get_json()
            preprocess_links = json_data.pop(self.links_keyword, None)
            if preprocess_links is None:
                return response
            elif not isinstance(preprocess_links, dict):
                raise TypeError("Malformed server response for resource linking")
            else:
                links_dict: TDesc = {}
                for field_name, field_data in preprocess_links.items():
                    resource_name, resource_val = field_data
                    link_view_func, link_bp = self.get_link_rule(resource_name)
                    args_rule = self.get_args_rule(resource_name)
                    if link_view_func is None:
                        raise TypeError(f"There is no link rule function registered for '{resource_name}'")
                    extra_args: TDesc = {}
                    if args_rule is not None:
                        extra_args.update(args_rule(resource_val))
                    url = (f"{link_bp.name}." if link_bp is not None else '') + link_view_func.__name__
                    resource_url = url_for(url, **extra_args)
                    links_dict[field_name] = resource_url
                json_data['links'] = links_dict
                return make_success_dict(response.status_code, data=json_data)
        return new_view_function

    def __repr__(self):
        func_dict = {k: (self.get_link_rule(k), self.get_args_rule(k)) for k in self.link_rules}
        return f"Linker <{func_dict}>"

    def __str__(self):
        return self.__repr__()


linker = Linker()


# utility for PyTorch device selection
def get_device():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


# utility for common datasets
def get_all_common_datasets_root(abspath: bool = False) -> str:
    basepath = os.path.join('common', 'datasets')
    return os.path.abspath(basepath) if abspath else os.path.relpath(basepath, os.getcwd())


def get_common_dataset_root(dataset_name: str, abspath: bool = False) -> str:
    basepath = os.path.join(get_all_common_datasets_root(abspath), dataset_name)
    return os.path.abspath(basepath) if abspath else os.path.relpath(basepath, os.getcwd())


# Exception catcher
def catcher(exc_type: t.Type[Exception] = Exception, dfl_return: t.Any = None):
    def wrapper(f: t.Callable):
        @wraps(f)
        def new_f(*args, **kwargs):
            # noinspection PyUnusedLocal, PyBroadException
            try:
                return f(*args, **kwargs)
            except exc_type as ex:
                traceback.print_exc(sys.exc_info())
                return dfl_return
        return new_f
    return wrapper


# Decorators for general TBoolExc behaviour
def auto_tboolexc(f: t.Callable):
    @wraps(f)
    def new_f(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as ex:
            return False, ex
    return new_f


# Decorators for general TBoolStr behaviour
def dfl_ex_str_callback(ex: Exception) -> str:
    return str(ex)


def auto_tboolstr(ex_str_callback: t.Callable = dfl_ex_str_callback):
    def wrapper(f: t.Callable):
        @wraps(f)
        def new_f(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as ex:
                traceback.print_exception(*sys.exc_info())
                msg = ex_str_callback(ex)
                return False, msg
        return new_f
    return wrapper


def normalize_map_field_path(s: str):
    return s.replace('.', '\\')


def denormalize_map_field_path(s: str):
    return s.replace('\\', '.')


# The following function is copied from an older version of the `Continual Learning Baselines` project.
# Current project GitHub page is: https://github.com/ContinualAI/continual-learning-baselines.
# Original function comments and citations are left unchanged.
def get_average_metric(metric_dict: dict, metric_name: str = 'Top1_Acc_Stream'):
    """
    Compute the average of a metric based on the provided metric name.
    The average is computed across the instance of the metrics containing the
    given metric name in the input dictionary.
    :param metric_dict: dictionary containing metric name as keys and metric value as value.
        This dictionary is usually returned by the `eval` method of Avalanche strategies.
    :param metric_name: the metric name (or a part of it), to be used as pattern to filter the dictionary
    :return: a number representing the average of all the metric containing `metric_name` in their name
    """

    avg_stream_acc = []
    for k, v in metric_dict.items():
        if k.startswith(metric_name):
            avg_stream_acc.append(v)
    return sum(avg_stream_acc) / float(len(avg_stream_acc))


__all__ = [
    'executor',

    'TBoolStr', 'TBoolExc', 'TDesc',
    'TBoolAny', 'TOptBoolAny',

    'os', 'abstractmethod', 'ABC',
    'datetime', 't', 'catcher',

    'GET', 'PUT', 'POST', 'PATCH',
    'OPTIONS', 'HEAD', 'DELETE',

    'auto_tboolstr',
    'auto_tboolexc',

    'make_success_kwargs',
    'make_success_dict',

    'checked_json',
    'check_json',
    'get_check_json_data',

    'LinkRule',
    'Linker',
    'linker',

    'get_device',
    'Module',

    'get_all_common_datasets_root',
    'get_common_dataset_root',

    'normalize_map_field_path',
    'denormalize_map_field_path',

    'get_average_metric',
]