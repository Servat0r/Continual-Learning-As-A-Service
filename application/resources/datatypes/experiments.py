"""
Interface for CL experiments.
"""
from __future__ import annotations

from application.utils import TDesc, t, abstractmethod
from application.resources.utils import JSONSerializable, URIBasedResource
from application.resources.base import ReferrableDataType

from .metricsets import BaseMetricSet


class BaseCLExperimentRunConfig:

    DFL_RUN_CONFIG_NAME = 'Std_Train_Test'

    __CONFIGS__: TDesc = {}

    @staticmethod
    def register_run_config(name: str = None):
        def registerer(cls):
            nonlocal name
            if name is None:
                name = cls.__name__
            BaseCLExperimentRunConfig.__CONFIGS__[name] = cls
            return cls

        return registerer

    @staticmethod
    def register_default_run_config():
        return BaseCLExperimentRunConfig.register_run_config(BaseCLExperimentRunConfig.DFL_RUN_CONFIG_NAME)

    @classmethod
    def get_by_name(cls, name: str | TDesc) -> BaseCLExperimentRunConfig | None:
        if isinstance(name, str):
            return cls.__CONFIGS__.get(name)
        elif isinstance(name, dict):
            cname = name.get('name')
            if cname is None:
                raise ValueError('Missing name')
            else:
                return cls.__CONFIGS__.get(cname)

    @classmethod
    def canonicalize(cls, obj: str | BaseCLExperimentRunConfig) -> BaseCLExperimentRunConfig | None:
        if isinstance(obj, BaseCLExperimentRunConfig):
            return obj
        else:
            return cls.get_by_name(obj)

    @abstractmethod
    def run(self, experiment: BaseCLExperiment, model_directory: list[str] = None) -> bool:
        pass


class BaseCLExperiment(ReferrableDataType):

    # 1. Fields
    CREATED = 'CREATED'
    READY = 'READY'
    RUNNING = 'RUNNING'
    ENDED = 'ENDED'

    # 3. General classmethods

    # 6. Instance methods

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

    def set_metadata(self, **kwargs):
        super().set_metadata(**kwargs)

    def get_metadata(self, key: str | None = None) -> TDesc | t.Any:
        return super().get_metadata(key)

    def run(self, model_directory: list[str] = None) -> bool | None:
        run_config = self.get_run_configuration()
        if run_config is None:
            return None
        else:
            return run_config.run(self, model_directory=model_directory)

    def is_running(self):
        return self.get_status() == self.RUNNING

    def is_done(self):
        return self.get_status() == self.ENDED

    @abstractmethod
    def get_run_configuration(self) -> BaseCLExperimentRunConfig:
        pass

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


class BaseCLExperimentExecution(JSONSerializable, URIBasedResource):

    @abstractmethod
    def get_exec_id(self) -> int:
        pass

    @abstractmethod
    def get_csv_results(self) -> tuple[bool, t.Optional[TDesc]]:
        pass

    @abstractmethod
    def get_final_model(self, descriptor=False):
        pass


__all__ = [
    'BaseCLExperimentRunConfig',
    'BaseCLExperiment',
    'BaseCLExperimentExecution',
]