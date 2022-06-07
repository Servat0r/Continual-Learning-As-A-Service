from __future__ import annotations

import time
import unittest

from ..data import *
from .base import *

# strategies
naive_strategy_build = generic_strategy_builder(
    'Naive',
    STD_MNIST_TRAIN_MB_SIZE,
    STD_MNIST_TRAIN_EPOCHS,
    STD_MNIST_EVAL_MB_SIZE,
)

cumulative_strategy_build = generic_strategy_builder(
    'Cumulative',
    STD_MNIST_TRAIN_MB_SIZE,
    STD_MNIST_TRAIN_EPOCHS,
    STD_MNIST_EVAL_MB_SIZE,
)

joint_training_strategy_build = generic_strategy_builder(
    'JointTraining',
    STD_MNIST_TRAIN_MB_SIZE,
    STD_MNIST_TRAIN_EPOCHS,
    STD_MNIST_EVAL_MB_SIZE,
)

replay_500_strategy_build = generic_strategy_builder(
    'Replay',
    STD_MNIST_TRAIN_MB_SIZE,
    STD_MNIST_TRAIN_EPOCHS,
    STD_MNIST_EVAL_MB_SIZE,
    memory=500,
)

replay_2500_strategy_build = generic_strategy_builder(
    'Replay',
    STD_MNIST_TRAIN_MB_SIZE,
    STD_MNIST_TRAIN_EPOCHS,
    STD_MNIST_EVAL_MB_SIZE,
    memory=2500,
)

gdumb_strategy_build = generic_strategy_builder(
    'GDumb',
    STD_MNIST_TRAIN_MB_SIZE,
    STD_MNIST_TRAIN_EPOCHS,
    STD_MNIST_EVAL_MB_SIZE,
    memory=500,
)

lwf_strategy_build = generic_strategy_builder(
    'LwF',
    STD_MNIST_TRAIN_MB_SIZE,
    STD_MNIST_TRAIN_EPOCHS,
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


class PermutedMNISTTest(BaseClassicBenchmarkExperimentTestCase):
    username = 'permuted-mnist-username'
    email = 'permuted_mnist' + BaseClassicBenchmarkExperimentTestCase.email
    password = BaseClassicBenchmarkExperimentTestCase.password
    workspace = 'permuted_mnist_workspace'

    num_iterations = 1
    current_directory_names = None

    # redefined since a test with permuted mnist could take a lot of time
    @property
    def result_folders(self) -> list[str]:
        if self.current_directory_names is None:
            now = time.time()
            self.current_directory_names = [f"exec_{now}"]
        return self.current_directory_names

    benchmark_build = {
        'name': 'PermutedMNIST',
        'n_experiences': 5,
        'seed': 0,
        'train_transform': {
            'name': 'TrainMNIST',
        },
        'eval_transform': {
            'name': 'EvalMNIST',
        }
    }

    model_build = {
        'name': 'SimpleMLP',
        'num_classes': 10,
        'input_size': 1 * 28 * 28,
        'hidden_layers': 2,
        'hidden_size': 512,
    }

    optimizer_build = sgd_optimizer_build
    criterion_build = criterion_build
    metricset_build = metricset_build

    def get_benchmark_name(self) -> str:
        return 'permuted_mnist_4_epochs'

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


if __name__ == '__main__':
    unittest.main(verbosity=2)