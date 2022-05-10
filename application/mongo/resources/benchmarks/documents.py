from __future__ import annotations

from application.utils import t, datetime
from application.models import User, Workspace

from application.resources.contexts import UserWorkspaceResourceContext
from application.resources.base import DataType, BaseMetadata

from application.mongo.utils import RWLockableDocument
from application.mongo.mongo_base_metadata import MongoBaseMetadata

from application.mongo.resources.mongo_base_configs import *
from application.mongo.base import MongoBaseUser, MongoBaseWorkspace


class BenchmarkMetadata(MongoBaseMetadata):
    pass


class MongoBenchmarkConfig(MongoResourceConfig):

    _COLLECTION = 'benchmarks'

    meta = {
        'collection': _COLLECTION,
        'indexes': [
            {'fields': ('owner', 'workspace', 'name'), 'unique': True}
        ]
    }

    @staticmethod
    def meta_type() -> t.Type[BaseMetadata]:
        return BenchmarkMetadata

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type("Benchmark")

    def __init__(self, *args, **values):
        super().__init__(*args, **values)

    @property
    def data_repository(self):
        build_config = self.build_config
        if hasattr(build_config, 'data_repository'):
            return build_config.data_repository
        else:
            return None

    @property
    def parents(self) -> set[RWLockableDocument]:

        data_repository = self.data_repository
        return {data_repository} if data_repository is not None else super().parents

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

            def __create():
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
                            obj.save(force_insert=True)
                return obj

            data_repository = build_config.data_repository
            if data_repository is not None:
                with data_repository.sub_resource_create(parents_locked=parents_locked):
                    return __create()
            else:
                with workspace.sub_resource_create(parents_locked=parents_locked):
                    return __create()


__all__ = [
    'BenchmarkMetadata',
    'MongoBenchmarkConfig',
]