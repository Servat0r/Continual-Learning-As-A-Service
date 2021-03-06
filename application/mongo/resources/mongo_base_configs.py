from __future__ import annotations

import sys
import traceback
from datetime import datetime
import schema as sch

from application.database import db
from application.utils import TBoolStr, TBoolExc, TDesc, abstractmethod, t, auto_tboolexc, auto_tboolstr
from application.validation import *
from application.models import User, Workspace

from application.resources.contexts import ResourceContext, UserWorkspaceResourceContext
from application.resources.base import EmbeddedBuildConfig, BuildConfig, ResourceConfig, BaseMetadata, DataType

from application.mongo.locking import RWLockableDocument
from application.mongo.mongo_base_metadata import MongoBaseMetadata
from application.mongo.base import MongoBaseUser, MongoBaseWorkspace


class MongoEmbeddedBuildConfig(db.EmbeddedDocument, EmbeddedBuildConfig):

    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    # Let's try to use schema
    @classmethod
    def schema_dict(cls) -> dict:
        return {
            'name': sch.And(str, validate_workspace_resource_experiment)
        }

    @abstractmethod
    def to_dict(self, links=True) -> TDesc:
        cls = type(self)
        name = cls.get_key()
        return {'name': name}

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
            data_copy.pop('name', None)

        for name in cls.get_required():
            val = data.get(name)
            if (val is not None) or cls.is_nullable(name):
                result[name] = val
                data_copy.pop(name, None)
            else:
                return False, bc_name, {}, {}

        for name in cls.get_optionals():
            val = data.get(name)
            if (val is not None) or cls.is_nullable(name):
                result[name] = val
                data_copy.pop(name, None)
        return True, bc_name, result, data_copy

    # noinspection PyUnusedLocal
    @classmethod
    @auto_tboolstr()
    def validate_input(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        """
        Base implementation of input validation where each parameter is accepted.
        :param data:
        :param context:
        :return:
        """
        schema = sch.Schema(cls.schema_dict())
        schema.validate(data)
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

    # Let's try to use schema
    @classmethod
    def schema_dict(cls) -> dict:
        return {
            'name': sch.And(str, validate_workspace_resource_experiment)
        }

    @abstractmethod
    def to_dict(self, links=True) -> TDesc:
        cls = type(self)
        name = cls.get_key()
        return {'name': name}

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
            data_copy.pop('name', None)

        for name in cls.get_required():
            val = data.get(name)
            if (val is not None) or cls.is_nullable(name):
                result[name] = val
                data_copy.pop(name, None)
            else:
                return False, bc_name, {}, {}

        for name in cls.get_optionals():
            val = data.get(name)
            if (val is not None) or cls.is_nullable(name):
                result[name] = val
                data_copy.pop(name, None)
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
        schema = sch.Schema(cls.schema_dict())
        schema.validate(data)
        return True, None
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
        """

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


class MongoBaseResourceConfig(RWLockableDocument, ResourceConfig):

    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    owner = db.ReferenceField(User.user_class())
    workspace = db.ReferenceField(Workspace.get_class())
    name = db.StringField(required=True)
    description = db.StringField(required=False)
    metadata = db.EmbeddedDocumentField(MongoBaseMetadata)

    # Let's try to use schema
    @classmethod
    @abstractmethod
    def schema_dict(cls) -> dict:
        return {
            'name': sch.And(str, validate_workspace_resource_experiment),
            sch.Optional('description'): str,
        }

    def __repr__(self):
        return f"{type(self).__name__} <id = {self.id}> [urn = {self.claas_urn}]"

    def __str__(self):
        return self.__repr__()

    @property
    def parents(self) -> set[RWLockableDocument]:
        """
        Objects from which the resource is dependent.
        :return:
        """
        return {self.workspace}

    @property
    def dependencies(self) -> dict[t.Type[MongoResourceConfig], str]:
        """
        Classes (collections) whose elements may depend on this resource.
        :return:
        """
        return {}

    # noinspection PyMethodMayBeStatic
    def extra_linked_dict_repr(self) -> TDesc:
        """
        Method used to add resource-specific fields to resource dict.
        MongoResourceConfig subclasses should redefine this method ONLY
        if they have extra fields or they want to include extra information.
        :return: A dictionary used for updating main representation dict in to_dict(...).
        """
        return {}

    def to_dict(self, links=True) -> TDesc:
        data = {
            'name': self.name,
            'description': self.description,
            'metadata': self.metadata.to_dict(),
        }
        data['metadata']['claas_urn'] = self.claas_urn
        if links:
            data['links'] = {
                'owner': ('User', self.owner),
                'workspace': ('Workspace', self.workspace)
            }
        else:
            data['owner'] = self.owner.get_name()
            data['workspace'] = self.workspace.get_name()
        extra = self.extra_linked_dict_repr()
        data.update(extra)
        return data

    @classmethod
    def get(cls, owner: str | MongoBaseUser = None, workspace: str | MongoBaseWorkspace = None,
            name: str = None, **args) -> list[MongoResourceConfig]:
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
                name: str = None, check_unique=False, **args) -> MongoResourceConfig | None:
        results = cls.get(owner, workspace, name, **args)
        if check_unique and len(results) > 1:
            raise RuntimeError("Query returned more than one result!")
        return results[0] if len(results) > 0 else None

    @classmethod
    def get_by_claas_urn(cls, urn: str):
        """
        urn is of the form "claas:<typename>:<username>:<workspace>:<resource_name>"
        :param urn:
        :return:
        """
        s = urn.split(cls.claas_urn_separator())
        owner = t.cast(MongoBaseUser, User.canonicalize(s[2]))
        workspace = Workspace.canonicalize((s[2], s[3]))
        name = s[4]
        ls = cls.get(owner=owner, workspace=workspace, name=name)
        return ls[0] if len(ls) > 0 else None

    @classmethod
    def all(cls):
        return list(cls.objects({}).all())

    @property
    def claas_urn(self):
        context = UserWorkspaceResourceContext(self.owner.get_name(), self.workspace.name)
        return type(self).dfl_claas_urn_builder(context, self.name)

    @classmethod
    def dfl_claas_urn_builder(cls, context: UserWorkspaceResourceContext, name: str) -> str:
        username = context.get_username()
        workspace = context.get_workspace()
        typename = cls.target_type().canonical_typename()
        return cls.claas_urn_separator().join(['claas', typename, username, workspace, name])

    @staticmethod
    @abstractmethod
    def target_type() -> t.Type[DataType]:
        pass

    @staticmethod
    @abstractmethod
    def meta_type() -> t.Type[BaseMetadata]:
        pass

    # noinspection PyUnusedLocal
    @classmethod
    def extra_create_params(cls, data, context: UserWorkspaceResourceContext, save=True,
                            parents_locked=False, metadata: dict = None) -> TDesc:
        return {}

    @classmethod
    def create(cls, data, context: UserWorkspaceResourceContext, save: bool = True,
               parents_locked=False, **metadata):
        result, msg = cls.validate_input(data, context)
        if not result:
            raise ValueError(msg)
        else:
            name = data['name']
            description = data.get('description', '')
            owner = t.cast(MongoBaseUser, User.canonicalize(context.get_username()))
            workspace = t.cast(MongoBaseWorkspace, Workspace.canonicalize(context))
            now = datetime.utcnow()

            if metadata is None:
                metadata = {}
            metadata['created'] = now
            metadata['last_modified'] = now

            extra = cls.extra_create_params(data, context, parents_locked=parents_locked, metadata=metadata, save=save)

            with workspace.sub_resource_create(parents_locked=parents_locked):
                # noinspection PyArgumentList
                obj = cls(
                    name=name,
                    description=description,
                    owner=owner,
                    workspace=workspace,
                    metadata=cls.meta_type()(**metadata),
                    **extra,
                )
                if obj is not None:
                    with obj.resource_create(parents_locked=True):
                        if save:
                            obj.save(create=True)
                return obj

    @classmethod
    @auto_tboolstr()
    def validate_input(cls, data, context: ResourceContext) -> TBoolStr:
        schema = sch.Schema(cls.schema_dict())
        schema.validate(data)
        return True, None

    @abstractmethod
    def build(self, context: ResourceContext,
              locked=False, parents_locked=False):
        pass

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

    def rename(self, old_name: str, new_name: str, save=False) -> TBoolStr:
        """
        Renames object.
        :param old_name:
        :param new_name:
        :param save:
        :return:
        """
        if not self.name == old_name:
            return False, "When updating name: old name and given one are not equal!"
        else:
            self.name = new_name
            try:
                self.update_last_modified(save=save)
                return True, None
            except Exception as ex:
                return False, ex.args[0]

    def update(self, data, context, save=True) -> TBoolStr:
        """
        Base method for updating
        :param data:
        :param context:
        :param save:
        :return:
        """
        new_name = data.get('name')
        new_desc = data.get('description')
        result, msg = validate_workspace_resource_experiment(new_name)
        if not result:
            return False, f"Invalid resource (new) name: '{new_name}'."

        if new_name is not None:
            data.pop('name')
            result, msg = self.rename(self.name, new_name, save=save)
            if not result:
                return result, f"When updating name: {msg}."

        if new_desc is not None:
            data.pop('description')
            if not isinstance(new_desc, str):
                return False, f"When updating description: must provide a string!"
            else:
                self.description = new_desc
                try:
                    self.update_last_modified(save=save)
                except Exception as ex:
                    print(ex)
                    return False, \
                           f"When updating description: an exception occurred: '{type(ex).__name__}': '{ex.args[0]}'."
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

    @auto_tboolexc
    def delete(self, context: UserWorkspaceResourceContext, locked=False, parents_locked=False) -> TBoolExc:
        with self.resource_delete(locked=locked, parents_locked=parents_locked):
            db.Document.delete(self)
            return True, None


class MongoResourceConfig(MongoBaseResourceConfig):

    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    build_config = db.EmbeddedDocumentField(MongoBuildConfig)

    @classmethod
    def schema_dict(cls) -> dict:
        result = super(MongoResourceConfig, cls).schema_dict()
        result.update({
            'build': {str: object},
        })
        return result

    @staticmethod
    @abstractmethod
    def target_type() -> t.Type[DataType]:
        pass

    @staticmethod
    @abstractmethod
    def meta_type() -> t.Type[BaseMetadata]:
        pass

    def to_dict(self, links=True) -> TDesc:
        data = super().to_dict(links=links)
        data['build'] = self.build_config.to_dict(links=False)
        extra = self.extra_linked_dict_repr()
        data.update(extra)
        return data

    @classmethod
    def extra_create_params(cls, data, context: UserWorkspaceResourceContext, save=True,
                            parents_locked=False, metadata: dict = None) -> TDesc:
        config = MongoBuildConfig.get_by_name(data['build'])
        if config is None:
            raise ValueError(f"Unknown build config: '{data['build']}'")
        build_config = t.cast(MongoBuildConfig, config).create(data['build'], cls.target_type(), context, save)
        return {'build_config': build_config}

    @classmethod
    def create(cls, data, context: UserWorkspaceResourceContext, save: bool = True,
               parents_locked=False, **metadata):
        return super(MongoResourceConfig, cls).create(data, context, save=save,
                                                      parents_locked=parents_locked, **metadata)

    @classmethod
    @auto_tboolstr()
    def validate_input(cls, data, context: ResourceContext) -> TBoolStr:
        schema = sch.Schema(cls.schema_dict())
        schema.validate(data)
        config = MongoBuildConfig.get_by_name(data['build'])
        return t.cast(MongoBuildConfig, config).validate_input(data['build'], cls.target_type(), context)

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

    def update(self, data, context, save=True) -> TBoolStr:
        result, msg = super().update(data, context, save=False)
        if not result:
            return result, f"Failed to update data: '{msg}'."
        new_build_config = data.get('build')
        if new_build_config is not None:
            data.pop('build')
            new_build_config.pop('name', None)    # Cannot modify build config!
            result, msg = self.build_config.update(new_build_config, context)
            if not result:
                return False, f"Failed to update build config: '{msg}'"
        self.update_last_modified(save=save)
        return True, None


__all__ = [
    'MongoEmbeddedBuildConfig',
    'MongoBuildConfig',
    'MongoBaseResourceConfig',
    'MongoResourceConfig',
]