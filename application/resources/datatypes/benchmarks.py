from __future__ import annotations

from avalanche.benchmarks import GenericCLScenario
from application.resources import *


class Benchmark(WrapperReferrableDataType, ABC):
    """
    A benchmark.
    """
    def __init__(self, benchmark: GenericCLScenario):
        super().__init__(benchmark)

    def set_metadata(self, **kwargs):
        WrapperReferrableDataType.set_metadata(self, **kwargs)

    def get_metadata(self, key: str | None = None) -> TDesc | t.Any:
        return WrapperReferrableDataType.get_metadata(self, key)