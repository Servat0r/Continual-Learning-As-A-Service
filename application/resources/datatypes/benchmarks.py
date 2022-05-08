from __future__ import annotations
from avalanche.benchmarks import GenericCLScenario

from application.utils import t, TDesc, ABC
from application.resources.base import WrapperReferrableDataType


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


__all__ = ['Benchmark']