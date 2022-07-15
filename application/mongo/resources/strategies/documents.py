from __future__ import annotations

from application.utils import t, datetime, TBoolExc, auto_tboolexc
from application.models import User, Workspace

from application.resources.contexts import UserWorkspaceResourceContext
from application.resources.base import DataType, ReferrableDataType, BaseMetadata

from application.mongo.locking import RWLockableDocument
from application.mongo.mongo_base_metadata import MongoBaseMetadata
from application.mongo.base import MongoBaseUser, MongoBaseWorkspace

from application.mongo.resources.mongo_base_configs import *
from application.mongo.resources.models import MongoModelConfig
from application.mongo.resources.metricsets import MongoStandardMetricSetConfig
from application.mongo.resources.optimizers import MongoCLOptimizerConfig
from application.mongo.resources.criterions import MongoCLCriterionConfig


class StrategyMetadata(MongoBaseMetadata):
    pass


class MongoStrategyConfig(MongoResourceConfig):

    _COLLECTION = 'strategies'

    meta = {
        'collection': _COLLECTION,
        'indexes': [
            {'fields': ('owner', 'workspace', 'name'), 'unique': True}
        ]
    }

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type("Strategy")

    @staticmethod
    def meta_type() -> t.Type[BaseMetadata]:
        return StrategyMetadata

    def __init__(self, *args, **values):
        super().__init__(*args, **values)

    @property
    def parents(self) -> set[RWLockableDocument]:
        build_config = self.build_config
        return {build_config.model, build_config.optimizer, build_config.criterion, build_config.metricset}

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

            model: MongoModelConfig = build_config.model
            optimizer: MongoCLOptimizerConfig = build_config.optimizer
            criterion: MongoCLCriterionConfig = build_config.criterion
            metricset: MongoStandardMetricSetConfig = build_config.metricset

            now = datetime.utcnow()

            if metadata is None:
                metadata = {}
            metadata['created'] = now
            metadata['last_modified'] = now

            with model.sub_resource_create(parents_locked=parents_locked):
                with optimizer.sub_resource_create(parents_locked=parents_locked):
                    with criterion.sub_resource_create(parents_locked=parents_locked):
                        with metricset.sub_resource_create(parents_locked=parents_locked):
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

    @auto_tboolexc
    def delete(self, context: UserWorkspaceResourceContext, locked=False, parents_locked=False) -> TBoolExc:
        with self.resource_delete(locked=locked, parents_locked=parents_locked):
            ExperimentClass = t.cast(ReferrableDataType, DataType.get_type('BaseCLExperiment')).config_type()
            experiments = ExperimentClass.get(build_config__strategy=self)
            for exp in experiments:
                exp.delete(context, parents_locked=True)
            return super().delete(context, locked=True, parents_locked=True)


__all__ = [
    'StrategyMetadata',
    'MongoStrategyConfig',
]