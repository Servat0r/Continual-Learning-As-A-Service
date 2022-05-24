from __future__ import annotations

from application.utils import t, datetime, TBoolExc, TBoolStr, catcher
from application.models import User, Workspace
from application.data_managing import BaseDataRepository

from application.resources.contexts import UserWorkspaceResourceContext
from application.resources.base import DataType, ReferrableDataType, BaseMetadata

from application.mongo.utils import RWLockableDocument
from application.mongo.mongo_base_metadata import MongoBaseMetadata

from application.mongo.resources.mongo_base_configs import *
from application.mongo.base import MongoBaseUser, MongoBaseWorkspace
from application.mongo.data_managing import MongoDataRepository


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
    def validate_input(cls, data, context: UserWorkspaceResourceContext) -> TBoolStr:
        return super(MongoBenchmarkConfig, cls).validate_input(data, context)

    @classmethod
    @catcher()
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

            def __create(cls):
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

            data_repository: MongoDataRepository | None = \
                BaseDataRepository.get_one(workspace=workspace, name=data['build'].get('data_repository'))

            build_config.data_repository = data_repository
            # data_repository = build_config.data_repository
            if data_repository is not None:
                with data_repository.sub_resource_create(parents_locked=parents_locked):
                    return __create(cls=cls)
            else:
                with workspace.sub_resource_create(parents_locked=parents_locked):
                    return __create(cls=cls)

    def delete(self, context: UserWorkspaceResourceContext, locked=False, parents_locked=False) -> TBoolExc:
        with self.resource_delete(locked=locked, parents_locked=parents_locked):
            try:
                ExperimentClass = t.cast(ReferrableDataType, DataType.get_type('BaseCLExperiment')).config_type()
                experiments = ExperimentClass.get(workspace=self.workspace)
                for exp in experiments:
                    exp.delete(context, parents_locked=True)
                return super().delete(context, locked=True, parents_locked=True)
            except Exception as ex:
                return False, ex


__all__ = [
    'BenchmarkMetadata',
    'MongoBenchmarkConfig',
]