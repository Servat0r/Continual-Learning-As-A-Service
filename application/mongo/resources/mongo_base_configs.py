from __future__ import annotations

import sys
import traceback
from datetime import datetime

from application.database import db
from application.utils import TBoolStr, TBoolExc, TDesc, abstractmethod, t
from application.validation import *
from application.models import User, Workspace

from application.resources.contexts import ResourceContext, UserWorkspaceResourceContext
from application.resources.base import BuildConfig, ResourceConfig, BaseMetadata, DataType

from application.mongo.locking import RWLockableDocument
from application.mongo.mongo_base_metadata import MongoBaseMetadata
from application.mongo.base import MongoBaseUser, MongoBaseWorkspace


class MongoEmbeddedBuildConfig(db.EmbeddedDocument):

    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    @classmethod
    @abstractmethod
    def get_required(cls) -> set[str]:
        return set()

    @classmethod
    @abstractmethod
    def get_optionals(cls) -> set[str]:
        return set()

    @classmethod
    def has_extras(cls) -> bool:
        """
        Checks whether this build config admits "extra" parameters
        (like keyword arguments in Python).
        :return:
        """
        return False  # By default, no extra arguments

    @classmethod
    def nullables(cls) -> set[str]:
        """
        Default implementation.
        :return:
        """
        return set()

    @classmethod
    def is_nullable(cls, name: str):
        return name in cls.nullables()

    @classmethod
    def names(cls) -> set[str]:
        return (cls.get_required() or set()).union(cls.get_optionals() or set())

    @classmethod
    def _filter_data(cls, data: TDesc) -> tuple[bool, str, TDesc, TDesc]:
        """
        Filters data in a given build config to given required, optionals and extras parameters passed.
        :param data:
        :return:
        """
        result: TDesc = {}
        data_copy = data.copy()

        bc_name = data_copy.get('name')
        if bc_name is not None:
            data_copy.pop('name')

        for name in cls.get_required():
            val = data.get(name)
            if (val is not None) or cls.is_nullable(name):
                result[name] = val
                data_copy.pop(name)
            else:
                return False, bc_name, {}, {}

        for name in cls.get_optionals():
            val = data.get(name)
            if (val is not None) or cls.is_nullable(name):
                result[name] = val
                data_copy.pop(name)
        return True, bc_name, result, data_copy

    # noinspection PyUnusedLocal
    @classmethod
    @abstractmethod
    def validate_input(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        """
        Base implementation of input validation where each parameter is accepted.
        :param data:
        :param context:
        :return:
        """
        ok, bc_name, params, extras = cls._filter_data(data)
        result, msg = validate_workspace_resource_experiment(bc_name)

        if not result:
            return False, f"Invalid resource name: '{bc_name}'."
        if not ok:
            return False, "Missing one or more required parameter(s)."
        if len(extras) > 0 and not cls.has_extras():
            return False, "Unexpected extra arguments."

        context.push('args', {'name': bc_name, 'params': params, 'extras': extras})
        return True, None

    # noinspection PyUnusedLocal
    @classmethod
    @abstractmethod
    def create(cls, data: TDesc, context: ResourceContext, save: bool = True):
        """
        Default implementation that assumes that ALL field names are equal to
        the corresponding ones in the JSON config sent by the client.
        :param data:
        :param context:
        :param save:
        :return:
        """
        ok, bc_name, params, extras = cls._filter_data(data)    # Validation "skipped"
        actuals: TDesc = params
        if cls.has_extras():
            for item in extras.items():
                actuals[item[0]] = item[1]
        # noinspection PyArgumentList
        return cls(**actuals)


class MongoBuildConfig(db.EmbeddedDocument, BuildConfig):

    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    def __init__(self, *args, **values):
        db.EmbeddedDocument.__init__(self, *args, **values)

    @classmethod
    @abstractmethod
    def get_required(cls) -> set[str]:
        return set()

    @classmethod
    @abstractmethod
    def get_optionals(cls) -> set[str]:
        return set()

    @classmethod
    def has_extras(cls) -> bool:
        """
        Checks whether this build config admits "extra" parameters
        (like keyword arguments in Python).
        :return:
        """
        return False  # By default, no extra arguments

    @classmethod
    def nullables(cls) -> set[str]:
        """
        Default implementation.
        :return:
        """
        return set()

    @classmethod
    def is_nullable(cls, name: str):
        return name in cls.nullables()

    @classmethod
    def names(cls) -> set[str]:
        return (cls.get_required() or set()).union(cls.get_optionals() or set())

    @classmethod
    def _filter_data(cls, data: TDesc) -> tuple[bool, str, TDesc, TDesc]:
        """
        Filters data in a given build config to given required, optionals and extras parameters passed.
        :param data:
        :return:
        """
        result: TDesc = {}
        data_copy = data.copy()

        bc_name = data_copy.get('name')
        if bc_name is not None:
            data_copy.pop('name')

        for name in cls.get_required():
            val = data.get(name)
            if (val is not None) or cls.is_nullable(name):
                result[name] = val
                data_copy.pop(name)
            else:
                return False, bc_name, {}, {}

        for name in cls.get_optionals():
            val = data.get(name)
            if (val is not None) or cls.is_nullable(name):
                result[name] = val
                data_copy.pop(name)
        return True, bc_name, result, data_copy

    # noinspection PyUnusedLocal
    @classmethod
    @abstractmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        """
        Base implementation of input validation where each parameter is accepted.
        :param data:
        :param dtype:
        :param context:
        :return:
        """
        try:
            ok, bc_name, params, extras = cls._filter_data(data)
            result, msg = validate_workspace_resource_experiment(bc_name)

            if not result:
                return False, f"Invalid resource name: '{bc_name}'."
            if not ok:
                return False, "Missing one or more required parameter(s)."
            if len(extras) > 0 and not cls.has_extras():
                return False, "Unexpected extra arguments."
            context.push('args', {'name': bc_name, 'params': params, 'extras': extras})
            return True, None
        except Exception as ex:
            traceback.print_exception(*sys.exc_info())
            return False, str(ex)

    # noinspection PyUnusedLocal
    @classmethod
    @abstractmethod
    def create(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext, save: bool = True):
        """
        Default implementation that assumes that ALL field names are equal to
        the corresponding ones in the JSON config sent by the client.
        :param data:
        :param dtype:
        :param context:
        :param save:
        :return:
        """
        ok, bc_name, params, extras = cls._filter_data(data)    # Validation "skipped"
        actuals: TDesc = params
        if cls.has_extras():
            for item in extras.items():
                actuals[item[0]] = item[1]
        # noinspection PyArgumentList
        return cls(**actuals)

    @staticmethod
    @abstractmethod
    def target_type() -> t.Type[DataType]:
        pass

    @abstractmethod
    def build(self, context: ResourceContext, locked=False, parents_locked=False):
        pass

    def update(self, data, context: ResourceContext) -> TBoolStr:
        try:
            if data is not None:
                for item in data.items():
                    exec(f"self.{item[0]} = {item[1]}")
            return True, None
        except Exception as ex:
            return False, f"When updating build config: an error occurred: '{type(ex).__name__}': {ex.args[0]}."


class MongoResourceConfig(RWLockableDocument, ResourceConfig):

    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    owner = db.ReferenceField(User.user_class())
    workspace = db.ReferenceField(Workspace.get_class())
    name = db.StringField(required=True)
    description = db.StringField(required=False)
    build_config = db.EmbeddedDocumentField(MongoBuildConfig)
    metadata = db.EmbeddedDocumentField(MongoBaseMetadata)

    def __repr__(self):
        return f"{type(self).__name__} <id = {self.id}> [uri = {self.uri}]"

    def __str__(self):
        return self.__repr__()

    @property
    def parents(self) -> set[RWLockableDocument]:
        return {self.workspace}

    # .................... #
    @classmethod
    def get(cls, owner: str | MongoBaseUser = None, workspace: str | MongoBaseWorkspace = None,
            name: str = None) -> list[MongoResourceConfig]:
        args = {}
        if owner is not None:
            owner = User.canonicalize(owner)
            args['owner'] = owner
        if isinstance(workspace, str):
            if owner is not None:
                workspace = Workspace.canonicalize((owner, workspace))
            else:
                raise RuntimeError("Unable to canonicalize workspace name: missing 'owner' parameter.")
        args['workspace'] = workspace
        if name is not None:
            args['name'] = name
        return list(cls.objects(**args).all())

    @classmethod
    def get_one(cls, owner: str | MongoBaseUser = None, workspace: str | MongoBaseWorkspace = None,
                name: str = None, check_unique=False) -> MongoResourceConfig | None:
        results = cls.get(owner, workspace, name)
        if check_unique and len(results) > 1:
            raise RuntimeError("Query returned more than one result!")
        return results[0] if len(results) > 0 else None

    @classmethod
    def get_by_uri(cls, uri: str):
        s = uri.split(cls.uri_separator())
        owner = t.cast(MongoBaseUser, User.canonicalize(s[1]))
        workspace = Workspace.canonicalize((s[1], s[2]))
        name = s[3]
        ls = cls.get(owner=owner, workspace=workspace, name=name)
        return ls[0] if len(ls) > 0 else None

    @classmethod
    def all(cls):
        return list(cls.objects({}).all())

    # .................... #

    @property
    def uri(self):
        context = UserWorkspaceResourceContext(self.owner.get_name(), self.workspace.name)
        return type(self).dfl_uri_builder(context, self.name)

    @classmethod
    def dfl_uri_builder(cls, context: UserWorkspaceResourceContext, name: str) -> str:
        username = context.get_username()
        workspace = context.get_workspace()
        typename = cls.target_type().canonical_typename()
        return cls.uri_separator().join([typename, username, workspace, name])

    # .................... #

    @staticmethod
    @abstractmethod
    def target_type() -> t.Type[DataType]:
        pass

    @staticmethod
    @abstractmethod
    def meta_type() -> t.Type[BaseMetadata]:
        pass

    @classmethod
    def create(cls, data, context: UserWorkspaceResourceContext, save: bool = True,
               parents_locked=False, **metadata):
        result, msg = cls.validate_input(data, context)
        if not result:
            raise ValueError(msg)
        else:
            name = data['name']
            description = data.get('description') or ''
            config = MongoBuildConfig.get_by_name(data['build'])
            if config is None:
                raise ValueError(f"Unknown build config: '{data['build']}'")

            build_config = t.cast(MongoBuildConfig, config).create(data['build'], cls.target_type(), context, save)
            owner = t.cast(MongoBaseUser, User.canonicalize(context.get_username()))
            workspace = t.cast(MongoBaseWorkspace, Workspace.canonicalize(context))
            now = datetime.utcnow()

            if metadata is None:
                metadata = {}
            metadata['created'] = now
            metadata['last_modified'] = now

            with workspace.sub_resource_create(parents_locked=parents_locked):
                # noinspection PyArgumentList
                obj = cls(
                    name=name,
                    description=description,
                    build_config=build_config,
                    owner=owner,
                    workspace=workspace,
                    metadata=cls.meta_type()(**metadata),
                )
                if obj is not None:
                    with obj.resource_create(parents_locked=True):
                        if save:
                            obj.save(create=True)
                return obj

    @classmethod
    def validate_input(cls, data, context: ResourceContext) -> TBoolStr:
        try:
            required = ['name', 'build']
            if not all(fname in data for fname in required):
                return False, 'Missing parameter(s).'
            else:
                name = data['name']
                result, msg = validate_workspace_resource_experiment(name)
                if not result:
                    return False, f"Invalid resource name: '{msg}'."
                config = MongoBuildConfig.get_by_name(data['build'])
                return t.cast(MongoBuildConfig, config).validate_input(data['build'], cls.target_type(), context)
        except Exception as ex:
            traceback.print_exception(*sys.exc_info())
            return False, str(ex)

    def build(self, context: ResourceContext,
              locked=False, parents_locked=False):
        with self.resource_read(locked=locked, parents_locked=parents_locked):
            obj = self.build_config.build(context, locked=True, parents_locked=True)
            obj.set_metadata(
                name=self.name,
                owner=self.owner.username,
                workspace=self.workspace.name,
                extra=self.metadata.to_dict()
            )
            return obj

    def get_name(self):
        return self.name

    def get_owner(self):
        return self.owner

    def get_workspace(self):
        return self.workspace

    def get_description(self):
        return self.description if self.description is not None else ''

    def update_last_modified(self, time: datetime = None, save: bool = True):
        self.metadata.update_last_modified(time)
        if save:
            self.save()

    def rename(self, old_name: str, new_name: str) -> TBoolStr:
        """
        Renames object.
        :param old_name:
        :param new_name:
        :return:
        """
        if not self.name == old_name:
            return False, "When updating name: old name and given one are not equal!"
        else:
            self.name = new_name
            try:
                self.save()
                self.update_last_modified()
                return True, None
            except Exception as ex:
                return False, ex.args[0]

    def update(self, data, context) -> TBoolStr:
        new_name = data.get('name')
        new_desc = data.get('description')
        new_build_config = data.get('build')

        result, msg = validate_workspace_resource_experiment(new_name)
        if not result:
            return False, f"Invalid resource (new) name: '{new_name}'."

        if new_name is not None:
            data.pop('name')
            result, msg = self.rename(self.name, new_name)
            if not result:
                return result, f"When updating name: {msg}."

        if new_desc is not None:
            data.pop('description')
            if not isinstance(new_desc, str):
                return False, f"When updating description: must provide a string!"
            else:
                self.description = new_desc
                try:
                    self.save()
                    self.update_last_modified()
                except Exception as ex:
                    print(ex)
                    return False, \
                           f"When updating description: an exception occurred: '{type(ex).__name__}': '{ex.args[0]}'."

        if new_build_config is not None:
            data.pop('build')
            return self.build_config.update(data, context)

        return True, None

    def save(self, create=False) -> bool:
        # noinspection PyUnusedLocal, PyBroadException
        try:
            if create:
                db.Document.save(self, force_insert=create)
            else:
                self.update_last_modified(save=False)
                db.Document.save(self, save_condition={'id': self.id})
            return True
        except Exception as ex:
            return False

    def delete(self, context: UserWorkspaceResourceContext, locked=False, parents_locked=False) -> TBoolExc:
        with self.resource_delete(locked=locked, parents_locked=parents_locked):
            try:
                db.Document.delete(self)
                return True, None
            except Exception as ex:
                return False, ex


__all__ = [
    'MongoEmbeddedBuildConfig',
    'MongoBuildConfig',
    'MongoResourceConfig',
]