from __future__ import annotations

from application.utils import t

from application.resources.contexts import UserWorkspaceResourceContext
from application.resources.base import DataType
from application.resources.datatypes import *

from application.mongo.resources.mongo_base_configs import *
from .documents import *


@DataType.set_resource_type()
class MongoCLExperiment(BaseCLExperiment):

    def __init__(self, strategy: Strategy, benchmark: Benchmark,
                 status: str, run_config: str | BaseCLExperimentRunConfig):
        super().__init__()
        self.strategy = strategy
        self.benchmark = benchmark
        self.status = status
        self.run_config = BaseCLExperimentRunConfig.canonicalize(run_config)

    def __repr__(self):
        return f"{type(self).__name__} ({super().__repr__()})."

    def __str__(self):
        return self.__repr__()

    # ReferrableDataType methods
    @staticmethod
    def config_type() -> t.Type[MongoResourceConfig]:
        return MongoCLExperimentConfig

    @classmethod
    def get_by_uri(cls, uri: str):
        return cls.config_type().get_by_uri(uri)

    @classmethod
    def dfl_uri_builder(cls, context: UserWorkspaceResourceContext, name: str) -> str:
        return cls.config_type().dfl_uri_builder(context, name)

    @classmethod
    def canonical_typename(cls) -> str:
        return BaseCLExperiment.canonical_typename()

    # BaseCLExperiment methods
    # Getters/Setters
    def get_benchmark(self):
        return self.benchmark

    def get_strategy(self):
        return self.strategy

    def get_model(self):
        return self.strategy.get_model()

    def get_optimizer(self):
        return self.strategy.get_optimizer()

    def get_criterion(self):
        return self.strategy.get_criterion()

    def get_metricset(self) -> BaseMetricSet:
        return self.strategy.get_metricset()

    def get_status(self) -> str:
        return self.status

    def get_run_configuration(self) -> BaseCLExperimentRunConfig:
        return self.run_config

    # ExperimentExecution methods
    def get_executions(self) -> t.Sequence[BaseCLExperimentExecution]:
        pass

    def get_execution(self, exec_id: int) -> BaseCLExperimentExecution:
        pass

    def get_current_execution(self):
        pass


__all__ = [
    'MongoCLExperiment',
]