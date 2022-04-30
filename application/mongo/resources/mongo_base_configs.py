from __future__ import annotations
from application.models import *
from application.resources import *
from application.mongo import *


class MongoBuildConfig(db.EmbeddedDocument, BuildConfig):

    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    @classmethod
    @abstractmethod
    def get_required(cls) -> set[str]:
        """
        Required parameters for this build config.
        :return:
        """
        pass

    @classmethod
    @abstractmethod
    def get_optionals(cls) -> set[str]:
        """
        Optional parameters for this build config.
        :return:
        """
        pass

    @classmethod
    def has_extras(cls) -> bool:
        """
        Checks whether this build config admits "extra" parameters
        (like keyword arguments in Python).
        :return:
        """
        return False    # By default, no extra arguments

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

    @staticmethod
    @abstractmethod
    def target_type() -> t.Type[DataType]:
        pass

    @classmethod
    def names(cls) -> set[str]:
        return (cls.get_required() or set()).union(cls.get_optionals() or set())

    @classmethod
    def _filter_data(cls, data: TDesc) -> tuple[bool, TDesc, TDesc]:
        """
        Filters data in a given build config to given required, optionals and extras parameters passed.
        :param data:
        :return:
        """
        result: TDesc = {}
        data_copy = data.copy()
        # TODO Refactor to 'name' and 'data' fields and analyze 'data' subdict!
        data_copy.pop('name')

        for name in cls.get_required():
            val = data.get(name)
            if (val is not None) or cls.is_nullable(name):
                result[name] = val
                data_copy.pop(name)
            else:
                return False, {}, {}

        for name in cls.get_optionals():
            val = data.get(name)
            if (val is not None) or cls.is_nullable(name):
                result[name] = val
                data_copy.pop(name)
        return True, result, data_copy

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
        ok, params, extras = cls._filter_data(data)
        if not ok:
            return False, "Missing one or more required parameter(s)."
        if len(extras) > 0 and not cls.has_extras():
            return False, "Unexpected extra arguments."
        context.push('args', {'params': params, 'extras': extras})
        return True, None

    @classmethod
    @abstractmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: ResourceContext, save: bool = True):
        """
        Default implementation that assumes that ALL field names are equal to
        the corresponding ones in the JSON config sent by the client.
        :param data:
        :param tp:
        :param context:
        :param save:
        :return:
        """
        result, msg = cls.validate_input(data, tp, context)
        if not result:
            raise ValueError(f"Input validation error: '{msg}'.")

        _, values = context.pop()
        actuals: TDesc = values['params']
        if cls.has_extras():
            extras: TDesc = values['extras']
            for item in extras.items():
                actuals[item[0]] = item[1]
        # noinspection PyArgumentList
        return cls(**actuals)

    @abstractmethod
    def build(self, context: ResourceContext):
        pass

    @abstractmethod
    def update(self, data, context: ResourceContext):
        pass

    def delete(self, context: ResourceContext):
        """
        Default implementation.
        :param context:
        :return:
        """
        db.EmbeddedDocument.delete(self)


class MongoResourceConfig(db.Document, ResourceConfig):

    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    name = db.StringField(required=True)
    uri = db.StringField(required=True, unique=True)
    description = db.StringField(required=False)
    build_config = db.EmbeddedDocumentField(MongoBuildConfig)
    metadata = db.EmbeddedDocumentField(MongoBaseMetadata)
    owner = db.ReferenceField(User.user_class())
    workspace = db.ReferenceField(Workspace.get_class())

    @classmethod
    def get_by_uri(cls, uri: str):
        return cls.objects(uri=uri).first()

    @classmethod
    def dfl_uri_builder(cls, context: UserWorkspaceResourceContext, name: str) -> str:
        username = context.get_username()
        workspace = context.get_workspace()
        typename = cls.target_type().canonical_typename()
        return cls.uri_separator().join([typename, username, workspace, name])

    @staticmethod
    @abstractmethod
    def target_type() -> t.Type[DataType]:
        pass

    @staticmethod
    @abstractmethod
    def meta_type() -> t.Type[BaseMetadata]:
        pass

    @classmethod
    def create(cls, data, context: UserWorkspaceResourceContext, save: bool = True, **metadata):
        result, msg = cls.validate_input(data, context)
        if not result:
            raise ValueError(msg)
        else:
            name = data['name']
            description = data['description'] or ''
            config = MongoBuildConfig.get_by_name(data['build'])
            if config is None:
                raise ValueError(f"Unknown build config: '{data['build']}'")

            build_config = t.cast(MongoBuildConfig, config).create(data['build'], cls.target_type(), context, save)
            uri = cls.dfl_uri_builder(context, name)
            owner = User.canonicalize(context.get_username())
            workspace = Workspace.canonicalize(context)
            now = datetime.utcnow()

            if metadata is None:
                metadata = {}
            metadata['created'] = now
            metadata['last_modified'] = now

            # noinspection PyArgumentList
            obj = cls(
                name=name,
                description=description,
                uri=uri,
                build_config=build_config,
                owner=owner,
                workspace=workspace,
                metadata=cls.meta_type()(**metadata),
            )
            if save:
                obj.save(force_insert=True)
            return obj

    @classmethod
    def validate_input(cls, data, context: ResourceContext) -> TBoolStr:
        required = ['name', 'build']
        if not all(fname in data for fname in required):
            return False, 'Missing parameter(s).'
        else:
            config = MongoBuildConfig.get_by_name(data['build'])
            return t.cast(MongoBuildConfig, config).validate_input(data['build'], cls.target_type(), context)

    def build(self, context: ResourceContext):
        obj = self.build_config.build(context)
        obj.set_metadata(
            name=self.name,
            uri=self.uri,
            owner=self.owner.username,
            workspace=self.workspace.name,
            extra=self.metadata.to_dict()
        )
        return obj

    @abstractmethod
    def update(self, data, context):
        pass

    def delete(self, context):
        db.Document.delete(self)

    def __init__(self, *args, **values):
        db.Document.__init__(self, *args, **values)

    def __repr__(self):
        return f"{type(self).__name__} <{self.name}>[id = {self.id}, uri = {self.uri}]"

    def __str__(self):
        return self.__repr__()