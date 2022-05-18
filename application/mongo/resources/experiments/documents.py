from __future__ import annotations
from datetime import datetime
from flask import Response

from application.database import db
from application.utils import t, TBoolExc
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

from .executions import *


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

    executions = db.ListField(db.EmbeddedDocumentField(MongoCLExperimentExecutionConfig), default=[])
    current_exec_id = db.IntField(default=0)

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

    def get_execution(self, exec_id: int):
        if exec_id > self.current_exec_id:
            raise ValueError(f"{exec_id} is out of existing executions range.")
        else:
            return self.executions[exec_id-1]

    def get_last_execution(self):
        return self.get_execution(self.current_exec_id)

    def _next_exec_id(self):
        return self.current_exec_id + 1

    def base_dir(self) -> list[str]:
        workspace: Workspace = self.workspace
        return workspace.experiments_base_dir_parents() \
            + [
                workspace.experiments_base_dir(),
                f"Experiment_{self.id}",
            ]

    def get_logging_path(self, exec_id: int = None) -> list[str]:
        exec_id = self._next_exec_id() if exec_id is None else exec_id
        return self.base_dir() + [str(exec_id), 'logs']

    def to_dict(self, settings=False):
        base_result = {
            'name': self.name,
            'description': self.description,
            'owner': self.owner.to_dict(),
            'workspace': self.workspace.to_dict(),
            'benchmark': self.benchmark.name,
            'strategy': self.strategy.name,
            'status': self.status,
            'run_config': self.run_config,
            'current_exec_id': self.current_exec_id,
        }
        if not settings:
            base_result['executions'] = [execution.to_dict() for execution in self.executions]
        return base_result
    
    def setup(self, locked=False, parents_locked=False) -> bool:
        with self.resource_read(locked=locked, parents_locked=parents_locked):
            if self.status == BaseCLExperiment.RUNNING:
                raise RuntimeError("Experiment already running!")
            elif self.status == BaseCLExperiment.READY:
                return True
            else:
                return self.modify({}, build_config__status=BaseCLExperiment.READY)

    def set_started(self, locked=False, parents_locked=False) -> int | None:
        with self.resource_write(locked=locked, parents_locked=parents_locked):
            exec_id = self.current_exec_id + 1
            # noinspection PyArgumentList
            execution = MongoCLExperimentExecutionConfig(experiment=self, exec_id=exec_id, started=True)
            if self.status != BaseCLExperiment.READY:
                raise RuntimeError("Experiment is not ready: must setup before start running!")
            else:
                result = self.modify(
                    {}, build_config__status=BaseCLExperiment.RUNNING,
                    inc__current_exec_id=1,
                    push__executions=execution,
                )
                if result:
                    return exec_id
                else:
                    return None

    def set_finished(self, response: Response, locked=False, parents_locked=False) -> TBoolExc:
        with self.resource_read(locked=locked, parents_locked=parents_locked):
            try:
                execution = self.get_last_execution()
                if self.status != BaseCLExperiment.RUNNING:
                    raise RuntimeError("Experiment is not running!")
                else:
                    self.build_config.status = BaseCLExperiment.ENDED
                    execution.completed = True
                    status_code = response.status_code
                    payload = response.get_json()
                    execution.status_code = status_code
                    execution.payload = payload
                    self.save()
                    return True, None
            except Exception as ex:
                print(ex)
                return False, ex

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
                                obj.save(create=True)
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