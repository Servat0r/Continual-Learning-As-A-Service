from __future__ import annotations
from typing import Any
import unittest

from client import *

from tests.utils import *


class BaseExperimentTestCase(BaseTestCase):
    """
    Base class for experiment testing.
    """
    def __init__(
        self,
        benchmark_data: dict[str, Any],
        model_data: dict[str, Any],
        optimizer_data: dict[str, Any],
        criterion_data,
        in_folder: str = None,
    ):
        pass