from __future__ import annotations

from avalanche.benchmarks import GenericCLScenario
from application.resources import *


class Benchmark(WrapperReferrableDataType, ABC):
    """
    A benchmark.
    """
    def __init__(self, benchmark: GenericCLScenario):
        super().__init__(benchmark)
        self.metadata: TDesc = {}

    def set_metadata(self, **kwargs):
        for item in kwargs.items():
            self.metadata[item[0]] = item[1]

    def get_metadata(self, key: str | None = None) -> TDesc | t.Any:
        if key is None:
            return self.metadata.copy()
        else:
            return self.metadata[key]