"""
Generic testcase for verifying experiments correctness.
"""
from __future__ import annotations
import unittest

from ..data import *
from .base import *

STD_MNIST_TRAIN_EPOCHS = 1

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

ewc_replay_strategy_name = 'ewc_replay_strategy'
ewc_replay_strategy_build = generic_strategy_builder(
    'EWC',
    STD_MNIST_TRAIN_MB_SIZE,
    STD_MNIST_TRAIN_EPOCHS * 2,
    STD_MNIST_EVAL_MB_SIZE,
    ewc_lambda=2.0,
    plugins=[
        {
            'name': 'Replay',
            'memory': 200,
        }
    ]
)

# experiments
naive_experiment_build = generic_experiment_builder(naive_strategy_name, benchmark_name)
cumulative_experiment_build = generic_experiment_builder(cumulative_strategy_name, benchmark_name)
ewc_replay_experiment_name = 'ewc_replay_experiment'
ewc_replay_experiment_build = generic_experiment_builder(ewc_replay_strategy_name, benchmark_name)


class ExperimentTest(BaseClassicBenchmarkExperimentTestCase):

    username = 'experiment-test-username'
    email = 'experiment_test_' + BaseClassicBenchmarkExperimentTestCase.email
    password = BaseClassicBenchmarkExperimentTestCase.password
    workspace = 'experiment_test_workspace'
    final_delete = True

    num_iterations = 1
    benchmark_build = {
        'name': 'SplitMNIST',
        'n_experiences': 5,
        'shuffle': True,
        'fixed_class_order': list(range(10)),
        'return_task_id': False,
        'seed': 0,
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
        'hidden_size': 256,
        'drop_rate': 0.5,
    }

    optimizer_build = sgd_optimizer_build
    criterion_build = criterion_build
    metricset_build = metricset_build
    
    @staticmethod
    def get_benchmark_name() -> str:
        return 'experiment_test'

    experiment_data = [
        {
            'folder': 'ewc_replay',
            'strategy_name': ewc_replay_strategy_name,
            'strategy_build': ewc_replay_strategy_build,
            'experiment_name': ewc_replay_experiment_name,
            'experiment_build': ewc_replay_experiment_build,
        },
    ]


if __name__ == '__main__':
    unittest.main()