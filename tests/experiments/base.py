from __future__ import annotations

import os.path
from abc import abstractmethod

from client import *
from tests.utils import *
from .data import *


class BaseExperimentTestCase(BaseTestCase):
    """
    Base class for experiment testing.
    """
    # Redefine these attributes in subclasses
    num_iterations = 3
    username = 'base-experiment-username'
    email = EMAIL
    password = PASSWORD
    workspace = 'base_experiment_workspace'

    host = HOST
    port = PORT
    client = BaseClient(host, port)

    base_folder = STD_RESULTS_BASE_FOLDER
    csv_folder = STD_CSV_FOLDER_NAME
    models_folder = STD_MODELS_FOLDER_NAME

    benchmark_name = benchmark_name
    benchmark_build: dict = None  # redefine in subclasses before usage

    model_name = model_name
    model_build: dict = None  # redefine in subclasses before usage

    optimizer_name = optimizer_name
    optimizer_build: dict = None  # redefine in subclasses before usage

    criterion_name = criterion_name
    criterion_build = criterion_build

    metricset_name = metricset_name
    metricset_build = metricset_build

    experiment_data: list[dict[str, str | dict]] = []

    @staticmethod
    @abstractmethod
    def get_benchmark_name() -> str:    # split_mnist, split_cifar10, ...; used for directories
        pass

    def setUp(self) -> None:
        super().setUp()
        os.makedirs(self.base_folder, exist_ok=True)

    @abstractmethod
    def test_all_experiments(self):
        pass


__all__ = [
    'BaseExperimentTestCase',
]