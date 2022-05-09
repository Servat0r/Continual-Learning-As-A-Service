from __future__ import annotations

from application.utils import t

from application.resources.base import DataType, BaseMetadata
from application.resources.datatypes import BaseCLExperiment

from application.mongo.utils import RWLockableDocument
from application.mongo.mongo_base_metadata import MongoBaseMetadata
from application.mongo.resources.mongo_base_configs import *


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
        return DataType.get_type("CLExperiment")

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
    
    def setup(self, locked=False, all_locked=False, parents_locked: set[RWLockableDocument] = None) -> bool:
        parents_locked = self.parents if all_locked else parents_locked
        with self.resource_read(locked=locked, parents_locked=parents_locked):
            if self.status == BaseCLExperiment.RUNNING:
                raise RuntimeError("Experiment already running!")
            elif self.status == BaseCLExperiment.READY:
                return True
            else:
                return self.modify({}, status=BaseCLExperiment.READY)

    # TODO ExperimentExecution operations!
    def set_started(self, locked=False, all_locked=False, parents_locked: set[RWLockableDocument] = None) -> bool:
        parents_locked = self.parents if all_locked else parents_locked
        with self.resource_read(locked=locked, parents_locked=parents_locked):
            if self.status != BaseCLExperiment.READY:
                raise RuntimeError("Experiment is not ready: must setup before start running!")
            else:
                return self.modify({}, status=BaseCLExperiment.RUNNING)

    # TODO ExperimentExecution operations and thread/process stopping!
    def set_finished(self, locked=False, all_locked=False, parents_locked: set[RWLockableDocument] = None) -> bool:
        parents_locked = self.parents if all_locked else parents_locked
        with self.resource_read(locked=locked, parents_locked=parents_locked):
            if self.status != BaseCLExperiment.RUNNING:
                raise RuntimeError("Experiment is not running!")
            else:
                return self.modify({}, status=BaseCLExperiment.ENDED)


__all__ = [
    'CLExperimentMetadata',
    'MongoCLExperimentConfig',
]