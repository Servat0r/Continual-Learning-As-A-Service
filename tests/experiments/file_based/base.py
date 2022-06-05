from __future__ import annotations

import sys
import traceback
from typing import Optional
import json
import os.path
from time import sleep
from abc import abstractmethod

from tests.utils import *
from ..data import *
from ..base import *


# noinspection SpellCheckingInspection
class BaseFileBasedBenchmarkExperimentTestCase(BaseExperimentTestCase):
    """
    Base class for file-based benchmarks-based experiments testing
    (i.e., experiments that use file-based benchmarks build configs).
    """
    # Redefine these attributes in subclasses
    username = 'base-file-based-experiment-username'
    workspace = 'base_file_based_experiment_workspace'
    data_repository_name = 'repository'
    source_folder = 'source_datasets'

    num_classes = None
    _TRAIN_ITEMS_PER_CATEGORY = None
    _TEST_ITEMS_PER_CATEGORY = None

    @staticmethod
    @abstractmethod
    def get_benchmark_name() -> str:    # split_mnist, split_cifar10, ...; used for directories
        pass

    @staticmethod
    @abstractmethod
    def get_dataset_name() -> str:      # mnist, cifar10, cifar100, ...; used for data repository subdirs
        pass

    @time_measure()
    def send_files(self) -> tuple[bool, Optional[Exception]]:
        train_base_dir = [self.get_dataset_name(), 'train']
        test_base_dir = [self.get_dataset_name(), 'test']
        files_train_dict: list[tuple[str, str, int]] = []
        files_test_dict: list[tuple[str, str, int]] = []

        try:
            for i in range(self.num_classes):
                # files_train_dict: list[tuple[str, str, int]] = []
                basedir = os.path.join(self.source_folder, *train_base_dir, str(i))
                fnames = os.listdir(basedir)
                length = self._TRAIN_ITEMS_PER_CATEGORY
                fnames = fnames[:length] if length >= 0 else fnames
                for fname in fnames:
                    files_train_dict.append((os.path.join(basedir, fname), '/'.join([str(i), fname]), i))
                """
                self.assertBaseHandler(self.client.send_files(
                    self.data_repository_name, files_train_dict, train_base_dir, files_mode='zip',
                ))
                """

                # files_test_dict: list[tuple[str, str, int]] = []
                basedir = os.path.join(self.source_folder, *test_base_dir, str(i))
                fnames = os.listdir(basedir)
                length = self._TEST_ITEMS_PER_CATEGORY
                fnames = fnames[:length] if length >= 0 else fnames
                for fname in fnames:
                    files_test_dict.append((os.path.join(basedir, fname), '/'.join([str(i), fname]), i))
                """
                self.assertBaseHandler(self.client.send_files(
                    self.data_repository_name, files_test_dict, test_base_dir, files_mode='zip',
                ))
                """
            self.assertBaseHandler(self.client.send_files(
                self.data_repository_name, files_test_dict, test_base_dir, files_mode='zip', zip_file_name='test.zip',
            ))
            self.assertBaseHandler(self.client.send_files(
                self.data_repository_name, files_train_dict, train_base_dir, files_mode='zip', zip_file_name='train.zip',
            ))
            return True, None
        except Exception as ex:
            print(ex)
            traceback.print_exception(*sys.exc_info())
            return False, ex

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

            # data repository creation and file adding
            self.assertBaseHandler(self.client.create_data_repository(self.data_repository_name))

            self.assertBaseHandler(
                self.client.create_subdir(self.data_repository_name, self.get_dataset_name())
            )

            self.assertBaseHandler(
                self.client.create_subdir(self.data_repository_name, 'train', [self.get_dataset_name()])
            )

            self.assertBaseHandler(
                self.client.create_subdir(self.data_repository_name, 'test', [self.get_dataset_name()])
            )

            result, ex = self.send_files()
            self.assertTrue(result, str(ex.args) if ex is not None else '')

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


__all__ = [
    'BaseFileBasedBenchmarkExperimentTestCase',
]