from __future__ import annotations

from torch.optim import Optimizer
from application.utils import ABC, TDesc, t
from application.resources.base import WrapperReferrableDataType


class CLOptimizer(WrapperReferrableDataType, ABC):
    """
    A loss criterion.
    """
    def __init__(self, optimizer: Optimizer):
        super().__init__(optimizer)

    def set_metadata(self, **kwargs):
        WrapperReferrableDataType.set_metadata(self, **kwargs)

    def get_metadata(self, key: str | None = None) -> TDesc | t.Any:
        return WrapperReferrableDataType.get_metadata(self, key)


__all__ = ['CLOptimizer']