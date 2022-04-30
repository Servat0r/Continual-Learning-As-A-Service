from __future__ import annotations

from avalanche.models import BaseModel
from application.resources import *


class Model(WrapperReferrableDataType, ABC):
    """
    A benchmark.
    """
    def __init__(self, model: BaseModel):
        super().__init__(model)

    def set_metadata(self, **kwargs):
        WrapperReferrableDataType.set_metadata(self, **kwargs)

    def get_metadata(self, key: str | None = None) -> TDesc | t.Any:
        return WrapperReferrableDataType.get_metadata(self, key)