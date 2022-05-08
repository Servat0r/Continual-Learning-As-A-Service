from __future__ import annotations

from avalanche.training.strategies import *
from application.utils import ABC, TDesc, t
from application.resources.base import WrapperReferrableDataType


class Strategy(WrapperReferrableDataType, ABC):
    """
    General CL strategy.
    """
    def __init__(self, strategy: BaseStrategy):
        super().__init__(strategy)

    def set_metadata(self, **kwargs):
        WrapperReferrableDataType.set_metadata(self, **kwargs)

    def get_metadata(self, key: str | None = None) -> TDesc | t.Any:
        return WrapperReferrableDataType.get_metadata(self, key)


__all__ = ['Strategy']