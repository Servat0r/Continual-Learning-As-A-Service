from __future__ import annotations

from avalanche.training.templates import *
from application.utils import ABC, TDesc, t
from application.resources.base import WrapperReferrableDataType

from .models import Model
from .optimizers import CLOptimizer
from .criterions import CLCriterion
from .metricsets import StandardMetricSet


class Strategy(WrapperReferrableDataType, ABC):
    """
    General CL strategy.
    """
    def __init__(self, strategy: SupervisedTemplate,
                 model: Model, optimizer: CLOptimizer,
                 criterion: CLCriterion, metricset: StandardMetricSet):
        super().__init__(strategy)
        self.model = model
        self.optimizer = optimizer
        self.criterion = criterion
        self.metricset = metricset

    def set_metadata(self, **kwargs):
        WrapperReferrableDataType.set_metadata(self, **kwargs)

    def get_metadata(self, key: str | None = None) -> TDesc | t.Any:
        return WrapperReferrableDataType.get_metadata(self, key)

    def get_model(self) -> Model:
        return self.model

    def get_optimizer(self) -> CLOptimizer:
        return self.optimizer

    def get_criterion(self) -> CLCriterion:
        return self.criterion

    def get_metricset(self) -> StandardMetricSet:
        return self.metricset


__all__ = ['Strategy']