from __future__ import annotations

from application.utils import t, TDesc
from application.database import db
from application.models import Workspace

from application.resources.datatypes import Benchmark, BaseMetricSet,\
    Strategy, BaseCLExperiment, BaseCLExperimentExecution

from application.mongo.utils import RWLockableDocument
from application.mongo.mongo_base_metadata import MongoBaseMetadata
from application.mongo.resources import MongoStrategy


class MongoCLExperimentMetadata(MongoBaseMetadata):
    pass


class MongoCLExperimentExecution(BaseCLExperimentExecution, db.EmbeddedDocument):
    pass


class MongoCLExperiment(BaseCLExperiment, RWLockableDocument):

    _STATUS = (
        BaseCLExperiment.CREATED,
        BaseCLExperiment.READY,
        BaseCLExperiment.RUNNING,
        BaseCLExperiment.ENDED,
    )

    strategy = db.ReferenceField(MongoStrategy.config_type(), default=None)
    benchmark = db.ReferenceField(Benchmark.config_type(), default=None)
    status = db.StringField(choices=_STATUS, default=BaseCLExperiment.CREATED)
    executions = db.ListField(db.EmbeddedDocumentField(MongoCLExperimentExecution), default=[])
    workspace = db.ReferenceField(Workspace.get_class())
    current_execution = db.EmbeddedDocumentField(MongoCLExperimentExecution)

    def setup(self, strategy: Strategy, benchmark: Benchmark) -> bool:
        pass

    def run(self):
        pass

    def get_status(self) -> str:
        return self.status

    def get_executions(self) -> t.Sequence[BaseCLExperimentExecution]:
        pass

    def get_execution(self, exec_id: int) -> BaseCLExperimentExecution:
        pass

    def get_current_execution(self):
        pass

    def get_metricset(self) -> BaseMetricSet:
        return self.strategy

    def get_benchmark(self):
        pass

    def get_strategy(self):
        pass

    def get_model(self):
        pass

    def get_optimizer(self):
        pass

    def get_criterion(self):
        pass

    def to_dict(self) -> TDesc:
        pass

    @property
    def parents(self) -> set[RWLockableDocument]:
        pass


__all__ = [
    'MongoCLExperimentMetadata',
    'MongoCLExperimentExecution',
    'MongoCLExperiment',
]