from __future__ import annotations
from typing import Any

import sys
import traceback

from tests.utils import *
from ..data import *
from .base import *


_TEST_ITEMS_PER_CLASS = -1
_TRAIN_ITEMS_PER_CLASS = -1


# strategies
naive_strategy_build = generic_strategy_builder(
    'Naive',
    STD_MNIST_TRAIN_MB_SIZE,
    STD_MNIST_TRAIN_EPOCHS * 2,
    STD_MNIST_EVAL_MB_SIZE,
)

cumulative_strategy_build = generic_strategy_builder(
    'Cumulative',
    STD_MNIST_TRAIN_MB_SIZE,
    STD_MNIST_TRAIN_EPOCHS * 2,
    STD_MNIST_EVAL_MB_SIZE,
)

joint_training_strategy_build = generic_strategy_builder(
    'JointTraining',
    STD_MNIST_TRAIN_MB_SIZE,
    STD_MNIST_TRAIN_EPOCHS * 2,
    STD_MNIST_EVAL_MB_SIZE,
)

replay_500_strategy_build = generic_strategy_builder(
    'Replay',
    STD_MNIST_TRAIN_MB_SIZE,
    STD_MNIST_TRAIN_EPOCHS * 2,
    STD_MNIST_EVAL_MB_SIZE,
    memory=500,
)

replay_2500_strategy_build = generic_strategy_builder(
    'Replay',
    STD_MNIST_TRAIN_MB_SIZE,
    STD_MNIST_TRAIN_EPOCHS * 2,
    STD_MNIST_EVAL_MB_SIZE,
    memory=2500,
)

gdumb_strategy_build = generic_strategy_builder(
    'GDumb',
    STD_MNIST_TRAIN_MB_SIZE,
    STD_MNIST_TRAIN_EPOCHS * 2,
    STD_MNIST_EVAL_MB_SIZE,
    memory=500,
)

lwf_strategy_build = generic_strategy_builder(
    'LwF',
    STD_MNIST_TRAIN_MB_SIZE,
    STD_MNIST_TRAIN_EPOCHS * 2,
    STD_MNIST_EVAL_MB_SIZE,
    alpha=1.0,
    temperature=1.0,
)

# experiments
naive_experiment_build = generic_experiment_builder(naive_strategy_name, benchmark_name)
cumulative_experiment_build = generic_experiment_builder(cumulative_strategy_name, benchmark_name)
joint_training_experiment_build = generic_experiment_builder(
    joint_training_strategy_name,
    benchmark_name,
    run_config='JointTraining',
)
replay_500_experiment_build = generic_experiment_builder(replay_500_strategy_name, benchmark_name)
replay_2500_experiment_build = generic_experiment_builder(replay_2500_strategy_name, benchmark_name)
gdumb_experiment_build = generic_experiment_builder(gdumb_strategy_name, benchmark_name)
lwf_experiment_build = generic_experiment_builder(lwf_strategy_name, benchmark_name)


def generate_experience_benchmark_data(exp_num: int, classes_per_exp: int, dataset_base_dir: str,
                                       folder: str, num_items: int) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    files: list[str] = []
    supp_dict: dict[int, int] = {}
    for i in range(classes_per_exp):
        num = exp_num * classes_per_exp + i
        base_dir = os.path.join('source_datasets', dataset_base_dir, folder, str(num))
        files_in_dir = [s.split('.')[0] for s in os.listdir(base_dir)]
        files_in_dir = [int(s) for s in files_in_dir]
        files_in_dir = files_in_dir if num_items < 0 else files_in_dir[:num_items]
        for s in files_in_dir:
            supp_dict[s] = num  # that file belongs to that folder

    for file_num in sorted(supp_dict.keys()):
        dir_num = supp_dict[file_num]
        files.append(f"{dir_num}/{file_num}.png")

    description = {
        'root': f"{dataset_base_dir}/{folder}",
        'selected': {
            'all': False,
            'files': files,
        },
        'labels': {
            num: {
                'root': str(num),
                'all': True,
            } for num in range(exp_num * classes_per_exp, (exp_num + 1) * classes_per_exp)
        },
        'default_label': 0,
    }
    print(description)
    result.append(description)
    return result


class SplitMNISTFileBasedTest(BaseFileBasedBenchmarkExperimentTestCase):

    username = 'file-based-split-mnist-username'
    email = 'file_based_split_mnist' + BaseFileBasedBenchmarkExperimentTestCase.email
    password = BaseFileBasedBenchmarkExperimentTestCase.password
    workspace = 'file_based_split_mnist_workspace'
    data_repository_name = BaseFileBasedBenchmarkExperimentTestCase.data_repository_name

    num_classes = 10
    _TEST_ITEMS_PER_CATEGORY = _TEST_ITEMS_PER_CLASS
    _TRAIN_ITEMS_PER_CATEGORY = _TRAIN_ITEMS_PER_CLASS
    num_iterations = 3

    benchmark_build = {
        'name': "CustomFileBasedClassificationDatasetBenchmark",
        'data_repository': data_repository_name,
        'img_type': 'greyscale',
        'train_stream': [generate_experience_benchmark_data(exp, 2, 'mnist', 'train',
                                                            _TRAIN_ITEMS_PER_CLASS) for exp in range(5)],
        'test_stream': [generate_experience_benchmark_data(exp, 2, 'mnist', 'test',
                                                           _TEST_ITEMS_PER_CLASS) for exp in range(5)],
        'train_transform': {'name': 'TrainMNIST'},
        'eval_transform': {'name': 'EvalMNIST'},
    }

    model_build = {
        'name': 'SimpleMLP',
        'num_classes': 10,
        'input_size': 1 * 28 * 28,
        'hidden_layers': 1,
        'hidden_size': 512,
    }

    optimizer_build = sgd_optimizer_build
    criterion_build = criterion_build
    metricset_build = metricset_build

    @staticmethod
    def get_benchmark_name() -> str:    # split_mnist, split_cifar10, ...; used for directories
        return 'file_based_split_mnist_8_epovhs'

    @staticmethod
    def get_dataset_name() -> str:      # mnist, cifar10, cifar100, ...; used for data repository subdirs
        return 'mnist'

    experiment_data = [
        {
            'folder': 'naive',
            'strategy_name': naive_strategy_name,
            'strategy_build': naive_strategy_build,
            'experiment_name': naive_experiment_name,
            'experiment_build': naive_experiment_build,
        },
        {
            'folder': 'cumulative',
            'strategy_name': cumulative_strategy_name,
            'strategy_build': cumulative_strategy_build,
            'experiment_name': cumulative_experiment_name,
            'experiment_build': cumulative_experiment_build,
        },
        {
            'folder': 'joint_training',
            'strategy_name': joint_training_strategy_name,
            'strategy_build': joint_training_strategy_build,
            'experiment_name': joint_training_experiment_name,
            'experiment_build': joint_training_experiment_build,
        },
        {
            'folder': 'replay_500',
            'strategy_name': replay_500_strategy_name,
            'strategy_build': replay_500_strategy_build,
            'experiment_name': replay_500_experiment_name,
            'experiment_build': replay_500_experiment_build,
        },
        {
            'folder': 'replay_2500',
            'strategy_name': replay_2500_strategy_name,
            'strategy_build': replay_2500_strategy_build,
            'experiment_name': replay_2500_experiment_name,
            'experiment_build': replay_2500_experiment_build,
        },
        {
            'folder': 'lwf',
            'strategy_name': lwf_strategy_name,
            'strategy_build': lwf_strategy_build,
            'experiment_name': lwf_experiment_name,
            'experiment_build': lwf_experiment_build,
        },
    ]