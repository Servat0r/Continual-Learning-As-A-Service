from __future__ import annotations

from avalanche.evaluation.metric_definitions import *
from application.resources import *


class BaseMetricSet(WrapperReferrableDataType, ABC):
    """
    A set of metrics to be used for evaluating experiment.
    """
    def __init__(self, *metrics: t.Union[PluginMetric, t.Sequence[PluginMetric]]):
        metrics = tuple() if metrics is None else metrics
        super().__init__(metrics)
        self.metadata: TDesc = {}

    def set_metadata(self, **kwargs):
        for item in kwargs.items():
            self.metadata[item[0]] = item[1]

    def get_metadata(self, key: str | None = None) -> TDesc | t.Any:
        if key is None:
            return self.metadata.copy()
        else:
            return self.metadata[key]


class StandardMetricSet(BaseMetricSet, ABC):
    """
    Specialization of the base case where we consider ONLY
    standard metrics got by metrics helper functions.
    """
    pass