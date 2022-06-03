# Common data dicts for experiments
from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv('../test.env', override=True)

# Experiments and models results folder
# Directory tree should appear as following:
#   results/
#       <dataset_name>/     # e.g. "SplitMNIST"
#           <strategy_name>/
#               csv/
#                   train_results.csv
#                   eval_results.csv
#               models/
#                   model.pt    # final model after the experiment
STD_RESULTS_BASE_FOLDER = os.getenv('BASE_EXPERIMENTS_FOLDER', os.path.join('..', 'results'))
STD_CSV_FOLDER_NAME = 'csv'
STD_MODELS_FOLDER_NAME = 'models'
print(f"results base folder = '{STD_RESULTS_BASE_FOLDER}'")
print(os.getenv('DUMMY', 'n.d.'))


# Standard hyperparameters
# MNIST
STD_MNIST_TRAIN_MB_SIZE = 30
STD_MNIST_TRAIN_EPOCHS = 4
STD_MNIST_EVAL_MB_SIZE = 30
# CIFAR
STD_CIFAR_TRAIN_MB_SIZE = 25
STD_CIFAR_TRAIN_EPOCHS = 4
STD_CIFAR_EVAL_MB_SIZE = 25


# Standard basic resources names
benchmark_name = 'benchmark'
model_name = 'model'
optimizer_name = 'optimizer'
criterion_name = 'criterion'
metricset_name = 'metricset'

# Standard strategy names
naive_strategy_name = 'naive_strategy'
cumulative_strategy_name = 'cumulative_strategy'
joint_training_strategy_name = 'joint_training_strategy'
replay_500_strategy_name = 'replay_500_strategy'
replay_2500_strategy_name = 'replay_2500_strategy'
gdumb_strategy_name = 'gdumb_strategy'
lwf_strategy_name = 'lwf_strategy'
pnn_strategy_name = 'pnn_strategy'

# Standard experiment names
naive_experiment_name = 'naive_experiment'
cumulative_experiment_name = 'cumulative_experiment'
joint_training_experiment_name = 'joint_training_experiment'
replay_500_experiment_name = 'replay_500_experiment'
replay_2500_experiment_name = 'replay_2500_experiment'
gdumb_experiment_name = 'gdumb_experiment'
lwf_experiment_name = 'lwf_experiment'
pnn_experiment_name = 'pnn_experiment'

# Standard basic resources builds
metricset_build = {
    'name': "StandardMetricSet",
    'accuracy': {           # both train and evaluation
        'minibatch': True,
        'epoch': True,
        'experience': True,
        'stream': True,
    },
    'loss': {               # eval only
        'minibatch': True,
        'epoch': True,
        'experience': True,
        'stream': True,
        'eval_time': True,
    },
    'timing': {             # train only
        'minibatch': True,
        'epoch': True,
        'experience': True,
        'stream': True,
        'train_time': True,
    },
    'forgetting': {         # eval only
        'experience': True,
        'stream': True,
        'eval_time': True,
    },
    'ram_usage': {          # train only
        'minibatch': True,
        'epoch': True,
        'experience': True,
        'stream': True,
        'train_time': True,
    },
}

criterion_build = {
    'name': 'CrossEntropyLoss',
}

sgd_optimizer_build = {
    'name': 'SGD',
    'model': model_name,
    'learning_rate': 0.001,
    'momentum': 0.9,
}


# strategy and experiments builders
def generic_strategy_builder(
        name: str,
        train_mb_size: int,
        train_epochs: int,
        eval_mb_size: int,
        **extra_arguments,
):
    base_result = {
        'name': name,
        'model': model_name,
        'optimizer': optimizer_name,
        'criterion': criterion_name,
        'metricset': metricset_name,

        'train_mb_size': train_mb_size,
        'train_epochs': train_epochs,
        'eval_mb_size': eval_mb_size,
    }
    if extra_arguments is not None and len(extra_arguments) > 0:
        for arg_name, arg_value in extra_arguments.items():
            base_result[arg_name] = arg_value
    return base_result


def generic_experiment_builder(strategy: str, benchmark: str, name: str = 'ExperimentBuild', **kwargs):
    result = {
        'name': name,
        'strategy': strategy,
        'benchmark': benchmark,
    }
    for arg_name, arg_value in kwargs.items():
        result[arg_name] = arg_value
    return result