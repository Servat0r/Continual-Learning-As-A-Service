from application.mongo_resources.mongo_base_configs import *
from application.mongo_resources.commons_test.metadata import *


class MongoDummyDocument(MongoResourceConfig):

    @classmethod
    def get_by_uri(cls, uri: str):
        return MongoDummyDocument.objects(uri=uri).first()

    @classmethod
    def dfl_uri_builder(cls, context: UserWorkspaceResourceContext, name: str) -> str:
        username = context.get_username()
        workspace = context.get_workspace()
        typename = cls.target_type().canonical_typename()
        return cls.uri_separator().join([typename, username, workspace, name])

    @staticmethod
    def target_type():
        return DataType.get_type('Dummy')

    @classmethod
    def create(cls, data, context: UserWorkspaceResourceContext, save: bool = True):
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
            # noinspection PyArgumentList
            obj = cls(
                name=name,
                description=description,
                uri=uri,
                build_config=build_config,
                owner=owner,
                workspace=workspace,
                metadata=DummyMetadata(created=now, last_modified=now),
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

    def update(self, data, context):
        pass

    def delete(self, context):
        db.Document.delete(self)

    def __init__(self, *args, **values):
        MongoResourceConfig.__init__(self, *args, **values)

    def __repr__(self):
        return f"{type(self).__name__} <{self.name}>[id = {self.id}, uri = {self.uri}]"

    def __str__(self):
        return self.__repr__()


class MongoSuperDummyDocument(MongoResourceConfig):

    @classmethod
    def get_by_uri(cls, uri: str):
        return MongoSuperDummyDocument.objects(uri=uri).first()

    @classmethod
    def dfl_uri_builder(cls, context: UserWorkspaceResourceContext, name: str) -> str:
        username = context.get_username()
        workspace = context.get_workspace()
        typename = cls.target_type().canonical_typename()
        return cls.uri_separator().join([typename, username, workspace, name])

    @staticmethod
    def target_type():
        return DataType.get_type('SuperDummy')

    @classmethod
    def create(cls, data, context: UserWorkspaceResourceContext, save: bool = True):
        result, msg = cls.validate_input(data, context)
        if not result:
            raise ValueError()
        else:
            name = data['name']
            description = data['description'] or ''
            config = MongoBuildConfig.get_by_name(data['build'])
            if config is None:
                raise ValueError()
            build_config = t.cast(MongoBuildConfig, config).create(data['build'], cls.target_type(), context, save)
            uri = cls.dfl_uri_builder(context, name)
            owner = User.canonicalize(context.get_username())
            workspace = Workspace.canonicalize(context)
            now = datetime.utcnow()
            # noinspection PyArgumentList
            obj = cls(
                name=name,
                description=description,
                uri=uri,
                build_config=build_config,
                owner=owner,
                workspace=workspace,
                metadata=SuperDummyMetadata(created=now, last_modified=now),
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

    def update(self, data, context):
        pass

    def delete(self, context):
        db.Document.delete(self)

    def __init__(self, *args, **values):
        MongoResourceConfig.__init__(self, *args, **values)

    def __repr__(self):
        return f"MongoSuperDummyDocument <{self.name}> [id = {self.id}, uri = {self.uri}]"

    def __str__(self):
        return self.__repr__()