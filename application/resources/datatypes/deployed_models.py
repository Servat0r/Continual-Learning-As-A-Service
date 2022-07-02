from __future__ import annotations

from torch.nn import Module

from application.utils import ABC, TDesc, t, abstractmethod, TBoolStr
from application.resources.base import WrapperReferrableDataType
from application.resources.contexts import ResourceContext


class DeployedModel(WrapperReferrableDataType, ABC):
    """
    A deployed model that could be used for online predictions.
    """
    def __init__(self, model: Module):
        super().__init__(model)

    def set_metadata(self, **kwargs):
        WrapperReferrableDataType.set_metadata(self, **kwargs)

    def get_metadata(self, key: str | None = None) -> TDesc | t.Any:
        return WrapperReferrableDataType.get_metadata(self, key)

    def get_model(self) -> Module:
        return self.get_value()

    @abstractmethod
    def get_prediction(self, input_data, transform, **kwargs):
        pass


__all__ = [
    'DeployedModel',
]