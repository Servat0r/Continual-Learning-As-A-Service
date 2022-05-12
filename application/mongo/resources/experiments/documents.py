from __future__ import annotations
from datetime import datetime

from application.utils import t

from application.models import User, Workspace

from application.resources.contexts import UserWorkspaceResourceContext
from application.resources.base import DataType, BaseMetadata
from application.resources.datatypes import BaseCLExperiment

from application.mongo.utils import RWLockableDocument
from application.mongo.mongo_base_metadata import MongoBaseMetadata

from application.mongo.base import MongoBaseUser, MongoBaseWorkspace
from application.mongo.resources.mongo_base_configs import *
from application.mongo.resources.strategies import MongoStrategyConfig
from application.mongo.resources.benchmarks import MongoBenchmarkConfig


class CLExperimentMetadata(MongoBaseMetadata):
    pass


class MongoCLExperimentConfig(MongoResourceConfig):

    _COLLECTION = 'experiments'

    meta = {
        'collection': _COLLECTION,
        'indexes': [
            {'fields': ('owner', 'workspace', 'name'), 'unique': True}
        ]
    }

    # TODO Executions!

    @staticmethod
    def meta_type() -> t.Type[BaseMetadata]:
        return CLExperimentMetadata

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type("BaseCLExperiment")

    def __init__(self, *args, **values):
        super().__init__(*args, **values)

    @property
    def parents(self) -> set[RWLockableDocument]:
        return {self.benchmark, self.strategy}

    @property
    def benchmark(self):
        return self.build_config.benchmark
    
    @property
    def strategy(self):
        return self.build_config.strategy
    
    @property
    def status(self):
        return self.build_config.status

    @property
    def run_config(self) -> str:
        return self.build_config.run_config

    def get_logging_path(self) -> list[str]:
        workspace: Workspace = self.workspace
        return workspace.experiments_base_dir_parents() \
            + [
                workspace.experiments_base_dir(),
                str(self.id),
                'logs',
            ]

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'owner': self.owner.to_dict(),
            'workspace': self.workspace.to_dict(),
            'benchmark': self.benchmark.name,
            'strategy': self.strategy.name,
            'status': self.status,
            'run_config': self.run_config,
        }
    
    def setup(self, locked=False, parents_locked=False) -> bool:
        with self.resource_read(locked=locked, parents_locked=parents_locked):
            if self.status == BaseCLExperiment.RUNNING:
                raise RuntimeError("Experiment already running!")
            elif self.status == BaseCLExperiment.READY:
                return True
            else:
                return self.modify({}, build_config__status=BaseCLExperiment.READY)

    # TODO ExperimentExecution operations!
    def set_started(self, locked=False, parents_locked=False) -> bool:
        with self.resource_read(locked=locked, parents_locked=parents_locked):
            if self.status != BaseCLExperiment.READY:
                raise RuntimeError("Experiment is not ready: must setup before start running!")
            else:
                return self.modify({}, build_config__status=BaseCLExperiment.RUNNING)

    # TODO ExperimentExecution operations and thread/process stopping!
    def set_finished(self, locked=False, parents_locked=False) -> bool:
        with self.resource_read(locked=locked, parents_locked=parents_locked):
            if self.status != BaseCLExperiment.RUNNING:
                raise RuntimeError("Experiment is not running!")
            else:
                return self.modify({}, build_config__status=BaseCLExperiment.ENDED)

    @classmethod
    def create(cls, data, context: UserWorkspaceResourceContext, save: bool = True,
               parents_locked: bool = False, **metadata):

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

            benchmark: MongoBenchmarkConfig = build_config.benchmark
            strategy: MongoStrategyConfig = build_config.strategy

            with strategy.sub_resource_create(parents_locked=parents_locked):
                with benchmark.sub_resource_create(parents_locked=parents_locked):
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

    def build(self, context: UserWorkspaceResourceContext,
              locked=False, parents_locked=False):
        log_folder = self.get_logging_path()
        context.push('log_folder', log_folder)
        return super().build(context, locked, parents_locked)


__all__ = [
    'CLExperimentMetadata',
    'MongoCLExperimentConfig',
]