"""
Interface for CL experiments.
"""
from __future__ import annotations

from application.utils import ABC, TDesc, t, abstractmethod, Module
from application.resources.utils import JSONSerializable
from application.resources.base import ReferrableDataType
from .metricsets import BaseMetricSet
from .benchmarks import Benchmark
from .strategies import Strategy


class CLExperimentMixin(ABC):

    @abstractmethod
    def get_metricset(self) -> BaseMetricSet:
        pass

    @abstractmethod
    def get_benchmark(self):
        pass

    @abstractmethod
    def get_strategy(self):
        pass

    @abstractmethod
    def get_model(self):
        pass

    @abstractmethod
    def get_optimizer(self):
        pass

    @abstractmethod
    def get_criterion(self):
        pass


class BaseCLExperiment(CLExperimentMixin, ReferrableDataType, ABC):

    # 1. Fields
    CREATED = 'CREATED'
    READY = 'READY'
    RUNNING = 'RUNNING'
    ENDED = 'ENDED'

    # 3. General classmethods

    # 6. Instance methods
    def set_metadata(self, **kwargs):
        super().set_metadata(**kwargs)

    def get_metadata(self, key: str | None = None) -> TDesc | t.Any:
        return super().get_metadata(key)

    @abstractmethod
    def run(self):
        pass

    def is_running(self):
        return self.get_status() == self.RUNNING

    def is_done(self):
        return self.get_status() == self.ENDED

    @abstractmethod
    def get_status(self) -> str:
        pass

    @abstractmethod
    def get_executions(self) -> t.Sequence[BaseCLExperimentExecution]:
        pass

    @abstractmethod
    def get_execution(self, exec_id: int) -> BaseCLExperimentExecution:
        pass

    @abstractmethod
    def get_current_execution(self):
        pass


class BaseCLExperimentExecution(CLExperimentMixin):

    @abstractmethod
    def get_csv_results(self):
        pass

    @abstractmethod
    def get_final_model(self) -> Module:
        pass


__all__ = [
    'CLExperimentMixin',
    'BaseCLExperiment',
    'BaseCLExperimentExecution',
]