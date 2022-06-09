from __future__ import annotations
import unittest

from ..data import *
from .base import *

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


class SplitMNISTTest(BaseClassicBenchmarkExperimentTestCase):

    username = 'split-mnist-username'
    email = 'split_mnist' + BaseClassicBenchmarkExperimentTestCase.email
    password = BaseClassicBenchmarkExperimentTestCase.password
    workspace = 'split_mnist_workspace'

    benchmark_build = {
        'name': 'SplitMNIST',
        'n_experiences': 5,
        'shuffle': True,
        'fixed_class_order': list(range(10)),
        'return_task_id': True,
        # An example of composition
        'train_transform': {
            'name': 'Compose',
            'transforms': [
                {
                    'name': 'ToTensor',
                },
                {
                    'name': 'Normalize',
                    'mean': [0.1307],
                    'std': [0.3081],
                }
            ]
        },
        # An example of classic transform
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
    
    @staticmethod
    def get_benchmark_name() -> str:
        return 'split_mnist_8_epochs'

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