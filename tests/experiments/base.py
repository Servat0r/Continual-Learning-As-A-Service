from __future__ import annotations

import json
import os.path
from time import sleep
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

    @abstractmethod
    def get_benchmark_name(self) -> str:    # split_mnist, split_cifar10, ...; used for directories
        pass

    def setUp(self) -> None:
        super().setUp()
        os.makedirs(self.base_folder, exist_ok=True)

    @abstractmethod
    def test_all_experiments(self):
        pass


class BaseClassicBenchmarkExperimentTestCase(BaseExperimentTestCase):
    """
    Base class for classic benchmarks-based experiments testing
    (i.e., experiments that use classic benchmarks build configs).
    """
    # Redefine these attributes in subclasses
    username = 'base-classic-experiment-username'
    workspace = 'base_classic_experiment_workspace'

    @abstractmethod
    def get_benchmark_name(self) -> str:    # split_mnist, split_cifar10, ...; used for directories
        pass

    def test_all_experiments(self):
        with self.client.session(self.username, self.workspace):
            # register
            self.assertBaseHandler(
                self.client.register(self.username, self.email, self.password), success_codes=HTTPStatus.CREATED,
            )

            # login
            self.assertBaseHandler(self.client.login(self.username, self.password))

            # create workspace
            self.assertBaseHandler(self.client.create_workspace(self.workspace), success_codes=HTTPStatus.CREATED)

            # resource creation
            self.assertBaseHandler(self.client.create_benchmark(self.benchmark_name, self.benchmark_build),
                                   success_codes=HTTPStatus.CREATED)

            self.assertBaseHandler(self.client.create_metric_set(self.metricset_name, self.metricset_build),
                                   success_codes=HTTPStatus.CREATED)

            self.assertBaseHandler(self.client.create_model(self.model_name, self.model_build),
                                   success_codes=HTTPStatus.CREATED)

            self.assertBaseHandler(self.client.create_optimizer(self.optimizer_name, self.optimizer_build),
                                   success_codes=HTTPStatus.CREATED)

            self.assertBaseHandler(self.client.create_criterion(self.criterion_name, self.criterion_build),
                                   success_codes=HTTPStatus.CREATED)

            # strategies and experiments creation
            for descriptor in self.experiment_data:
                folder = descriptor['folder']
                strategy_name = descriptor['strategy_name']
                strategy_build = descriptor['strategy_build']

                experiment_name = descriptor['experiment_name']
                experiment_build = descriptor['experiment_build']

                # results/<benchmark_name>/<strategy_name>
                base_exp_dir = os.path.join(self.base_folder, self.get_benchmark_name())
                os.makedirs(base_exp_dir, exist_ok=True)

                self.assertBaseHandler(self.client.create_strategy(strategy_name, strategy_build),
                                       success_codes=HTTPStatus.CREATED)
                self.assertBaseHandler(self.client.create_experiment(experiment_name, experiment_build),
                                       success_codes=HTTPStatus.CREATED)

                for i in range(self.num_iterations):
                    results_dir = os.path.join(base_exp_dir, str(i), folder)
                    csv_dir = os.path.join(results_dir, self.csv_folder)
                    models_dir = os.path.join(results_dir, self.models_folder)

                    os.makedirs(results_dir, exist_ok=True)
                    os.makedirs(csv_dir, exist_ok=True)
                    os.makedirs(models_dir, exist_ok=True)

                    self.assertBaseHandler(self.client.setup_experiment(experiment_name))
                    self.assertBaseHandler(self.client.start_experiment(experiment_name))

                    # noinspection PyUnusedLocal
                    ok = False
                    while True:
                        sleep(5)
                        response = self.client.get_experiment_results(experiment_name)
                        self.assertBaseHandler(response, success_codes=(HTTPStatus.OK, HTTPStatus.LOCKED))
                        if response.status_code == HTTPStatus.OK:
                            ok = True
                            with open(os.path.join(results_dir, 'execution_results.json'), 'w') as f:
                                data = response.json()
                                json.dump(data, fp=f, indent=2)
                            break

                    if ok:
                        response = self.client.get_experiment_csv_results(experiment_name)
                        self.assertEqual(response.status_code, HTTPStatus.OK)
                        data = response.json()
                        train_csv = data.get('train', '')
                        eval_csv = data.get('eval', '')

                        with open(os.path.join(csv_dir, 'train_results.csv'), 'w') as f:
                            f.write(train_csv)
                        with open(os.path.join(csv_dir, 'eval_results.csv'), 'w') as f:
                            f.write(eval_csv)

                        response = self.client.get_experiment_model(experiment_name)
                        self.assertEqual(response.status_code, HTTPStatus.OK)
                        with open(os.path.join(models_dir, 'model.pt'), 'wb') as f:
                            f.write(response.content)
                        print(f"Saved model!")
                    print(f"Ended execution #{i+1}!")

            # close workspace
            self.assertBaseHandler(self.client.close_workspace())

            # delete workspace
            self.assertBaseHandler(self.client.delete_workspace())

            # delete user
            self.assertBaseHandler(self.client.delete_user())
