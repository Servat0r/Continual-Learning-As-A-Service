from __future__ import annotations

from avalanche.benchmarks import GenericCLScenario
from avalanche.training.strategies import BaseStrategy

from application.utils import t, TDesc

from application.resources.contexts import ResourceContext, UserWorkspaceResourceContext
from application.resources.base import DataType
from application.resources.datatypes import *

from application.mongo.resources.mongo_base_configs import *
from .documents import *


@DataType.set_resource_type()
class MongoCLExperiment(BaseCLExperiment):

    def __init__(self, strategy: Strategy, benchmark: Benchmark, status: str):
        super().__init__()
        self.strategy = strategy
        self.benchmark = benchmark
        self.status = status

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
        pass

    @classmethod
    def dfl_uri_builder(cls, *args, **kwargs) -> str:
        pass

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

    # ExperimentExecution methods
    def get_executions(self) -> t.Sequence[BaseCLExperimentExecution]:
        pass

    def get_execution(self, exec_id: int) -> BaseCLExperimentExecution:
        pass

    def get_current_execution(self):
        pass

    # Experiment running methods
    def run(self):
        cl_scenario: GenericCLScenario = self.get_benchmark().get_value()
        cl_strategy: BaseStrategy = self.get_strategy().get_value()

        train_stream = cl_scenario.train_stream
        test_stream = cl_scenario.test_stream

        results: list[TDesc] = []
        for experience in train_stream:
            cl_strategy.train(experience)
            results.append(cl_strategy.eval(test_stream))

        print(*results, sep='\n')   # TODO Replace with results registering!