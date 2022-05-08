from __future__ import annotations

from torch.nn.modules import Module
from application.utils import ABC, TDesc, t
from application.resources.base import WrapperReferrableDataType


class CLCriterion(WrapperReferrableDataType, ABC):
    """
    A loss criterion.
    """
    def __init__(self, criterion: Module):
        super().__init__(criterion)

    def set_metadata(self, **kwargs):
        WrapperReferrableDataType.set_metadata(self, **kwargs)

    def get_metadata(self, key: str | None = None) -> TDesc | t.Any:
        return WrapperReferrableDataType.get_metadata(self, key)


__all__ = ['CLCriterion']