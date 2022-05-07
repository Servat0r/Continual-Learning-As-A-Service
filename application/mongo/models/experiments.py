from __future__ import annotations
import os

from application.database import db
from application.resources import TDesc, t
from application.models import *
from application.mongo.mongo_base_metadata import *


class MongoCLExperimentMetadata(MongoBaseMetadata):
    pass


class MongoCLExperiment(BaseCLExperiment):

    @classmethod
    def create(cls, strategy: Strategy, model: Model, opt: Optimizer, criterion: Criterion, metrics: BaseMetricSet,
               benchmark: Benchmark) -> BaseCLExperiment | None:
        pass

    def delete(self):
        pass

    def setup(self, strategy: Strategy, model: Model, opt: Optimizer, criterion: Criterion, metrics: BaseMetricSet,
              benchmark: Benchmark) -> bool:
        pass

    def get_settings(self):
        pass

    def get_status(self):
        pass

    def get_models(self):
        pass

    def get_model(self, exec_id: int):
        pass

    def get_executions(self):
        pass

    def get_execution(self, exec_id: int):
        pass

    def get_metricset(self):
        pass

    def get_csv_results(self):
        pass

    def get_owner(self):
        pass

    def get_workspace(self):
        pass

    def get_data_repository(self):
        pass

    def to_dict(self) -> TDesc:
        pass