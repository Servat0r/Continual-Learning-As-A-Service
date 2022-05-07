"""
Interface for CL experiments.
"""
from __future__ import annotations
from application.resources import *


class BaseCLExperiment(JSONSerializable):

    # 0.0 Actual class methods
    __experiment_class__: t.Type[BaseCLExperiment] = None

    @staticmethod
    def set_class(cls):
        if BaseCLExperiment.__data_repo_class__ is None:
            BaseCLExperiment.__data_repo_class__ = cls
        return cls

    @staticmethod
    def get_class():
        return BaseCLExperiment.__experiment_class__

    # 3. General classmethods

    # 4. Create + callbacks
    @classmethod
    @abstractmethod
    def create(cls, strategy: Strategy, benchmark: Benchmark) -> BaseCLExperiment | None:
        pass

    # 5. Delete + callbacks
    @abstractmethod
    def delete(self):
        pass

    # 6. Instance methods
    @abstractmethod
    def setup(self, strategy: Strategy, benchmark: Benchmark) -> bool:
        pass

    @abstractmethod
    def get_settings(self):
        pass

    @abstractmethod
    def get_status(self):
        pass

    @abstractmethod
    def get_models(self):
        pass

    @abstractmethod
    def get_model(self, exec_id: int):
        pass

    @abstractmethod
    def get_executions(self):
        pass

    @abstractmethod
    def get_execution(self, exec_id: int):
        pass

    @abstractmethod
    def get_metricset(self):
        pass

    @abstractmethod
    def get_csv_results(self):
        pass

    @abstractmethod
    def get_owner(self):
        pass

    @abstractmethod
    def get_workspace(self):
        pass

    @abstractmethod
    def get_data_repository(self):
        pass

    @abstractmethod
    def to_dict(self) -> TDesc:
        pass


class BaseCLExperimentExecution(JSONSerializable):
    pass    # TODO Magari cancellare!