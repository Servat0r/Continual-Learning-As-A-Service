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

    def set_metadata(self, **kwargs):
        WrapperReferrableDataType.set_metadata(self, **kwargs)

    def get_metadata(self, key: str | None = None) -> TDesc | t.Any:
        return WrapperReferrableDataType.get_metadata(self, key)


class StandardMetricSet(BaseMetricSet, ABC):
    """
    Specialization of the base case where we consider ONLY
    standard metrics got by metrics helper functions.
    """
    pass