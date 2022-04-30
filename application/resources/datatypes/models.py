from __future__ import annotations

from avalanche.models import BaseModel
from application.resources import *


class Model(WrapperReferrableDataType, ABC):
    """
    A benchmark.
    """
    def __init__(self, model: BaseModel):
        super().__init__(model)
        self.metadata: TDesc = {}

    def set_metadata(self, **kwargs):
        for item in kwargs.items():
            self.metadata[item[0]] = item[1]

    def get_metadata(self, key: str | None = None) -> TDesc | t.Any:
        if key is None:
            return self.metadata.copy()
        else:
            return self.metadata[key]