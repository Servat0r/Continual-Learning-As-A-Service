from __future__ import annotations
import unittest
import time

from ..data import *
from .base import *

# strategies
naive_strategy_build = generic_strategy_builder(
    'Naive',
    STD_TINY_IMAGENET_TRAIN_MB_SIZE,
    STD_TINY_IMAGENET_TRAIN_EPOCHS * 2,
    STD_TINY_IMAGENET_EVAL_MB_SIZE,
)

cumulative_strategy_build = generic_strategy_builder(
    'Cumulative',
    STD_TINY_IMAGENET_TRAIN_MB_SIZE,
    STD_TINY_IMAGENET_TRAIN_EPOCHS * 2,
    STD_TINY_IMAGENET_EVAL_MB_SIZE,
)

joint_training_strategy_build = generic_strategy_builder(
    'JointTraining',
    STD_TINY_IMAGENET_TRAIN_MB_SIZE,
    STD_TINY_IMAGENET_TRAIN_EPOCHS * 2,
    STD_TINY_IMAGENET_EVAL_MB_SIZE,
)

replay_500_strategy_build = generic_strategy_builder(
    'Replay',
    STD_TINY_IMAGENET_TRAIN_MB_SIZE,
    STD_TINY_IMAGENET_TRAIN_EPOCHS * 2,
    STD_TINY_IMAGENET_EVAL_MB_SIZE,
    memory=500,
)

replay_2500_strategy_build = generic_strategy_builder(
    'Replay',
    STD_TINY_IMAGENET_TRAIN_MB_SIZE,
    STD_TINY_IMAGENET_TRAIN_EPOCHS * 2,
    STD_TINY_IMAGENET_EVAL_MB_SIZE,
    memory=2500,
)

gdumb_strategy_build = generic_strategy_builder(
    'GDumb',
    STD_TINY_IMAGENET_TRAIN_MB_SIZE,
    STD_TINY_IMAGENET_TRAIN_EPOCHS * 2,
    STD_TINY_IMAGENET_EVAL_MB_SIZE,
    memory=500,
)

lwf_strategy_build = generic_strategy_builder(
    'LwF',
    STD_TINY_IMAGENET_TRAIN_MB_SIZE,
    STD_TINY_IMAGENET_TRAIN_EPOCHS * 2,
    STD_TINY_IMAGENET_EVAL_MB_SIZE,
    alpha=10.0,
    temperature=2.0,
)

si_strategy_name = 'synaptic_intelligence_strategy'
si_strategy_build = generic_strategy_builder(
    'SynapticIntelligence',
    STD_MNIST_TRAIN_MB_SIZE,
    STD_MNIST_TRAIN_EPOCHS * 2,
    STD_MNIST_EVAL_MB_SIZE,
    si_lambda=1.0,
    eps=0.001,
)

ewc_strategy_name = 'ewc_strategy'
ewc_strategy_build = generic_strategy_builder(
    'EWC',
    STD_MNIST_TRAIN_MB_SIZE,
    STD_MNIST_TRAIN_EPOCHS * 2,
    STD_MNIST_EVAL_MB_SIZE,
    ewc_lambda=1.0,
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
si_experiment_name = 'synaptic_intelligence_experiment'
si_experiment_build = generic_experiment_builder(si_strategy_name, benchmark_name)

ewc_experiment_name = 'ewc_experiment'
ewc_experiment_build = generic_experiment_builder(ewc_strategy_name, benchmark_name)


class SplitTinyImageNetMultiHeadMLPTest(BaseClassicBenchmarkExperimentTestCase):
    username = 'split-tiny-imagenet-username'
    email = 'split_tiny_imagenet' + BaseClassicBenchmarkExperimentTestCase.email
    password = BaseClassicBenchmarkExperimentTestCase.password
    workspace = 'split_tiny_imagenet_workspace'

    num_iterations = 1  # unknown iteration time!
    current_directory_names = None

    # redefined as for PermutedMNIST for the same reasons
    @property
    def result_folders(self) -> list[str]:
        if self.current_directory_names is None:
            now = time.time()
            self.current_directory_names = [f"exec_{now}"]
        return self.current_directory_names


    benchmark_build = {
        'name': 'SplitTinyImageNet',
        'n_experiences': 10,
        'fixed_class_order': list(range(200)),
        'return_task_id': True,
        'seed': 0,
        'train_transform': {
            'name': 'TrainTinyImageNet',
        },
        'eval_transform': {
            'name': 'EvalTinyImageNet',
        }
    }

    model_build = {
        'name': 'MultiHeadMLP',
        'input_size': 3 * 64 * 64,
        'hidden_layers': 2,
        'hidden_size': 256,
    }

    optimizer_build = sgd_optimizer_build
    criterion_build = criterion_build
    metricset_build = metricset_build

    @staticmethod
    def get_benchmark_name() -> str:
        return 'split_tiny_imagenet_multihead_mlp_10_epochs_with_ewc'

    experiment_data = [
        {
            'folder': 'ewc',
            'strategy_name': ewc_strategy_name,
            'strategy_build': ewc_strategy_build,
            'experiment_name': ewc_experiment_name,
            'experiment_build': ewc_experiment_build,
        },
    ]

    experiment_data_bak = [
        {
            'folder': 'ewc',
            'strategy_name': ewc_strategy_name,
            'strategy_build': ewc_strategy_build,
            'experiment_name': ewc_experiment_name,
            'experiment_build': ewc_experiment_build,
        },
        {
            'folder': 'lwf',
            'strategy_name': lwf_strategy_name,
            'strategy_build': lwf_strategy_build,
            'experiment_name': lwf_experiment_name,
            'experiment_build': lwf_experiment_build,
        },
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
    ]


joint_training_experiment_data = {
    'folder': 'joint_training',
    'strategy_name': joint_training_strategy_name,
    'strategy_build': joint_training_strategy_build,
    'experiment_name': joint_training_experiment_name,
    'experiment_build': joint_training_experiment_build,
}


if __name__ == '__main__':
    unittest.main(verbosity=2)