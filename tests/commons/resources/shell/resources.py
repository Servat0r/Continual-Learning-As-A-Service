from __future__ import annotations
import unittest
from application import *

from tests.utils import *
from .base import *


# common parameters
_TRAIN_MB_SIZE = 30
_TRAIN_EPOCHS = 2
_EVAL_MB_SIZE = 30

_WIDTH = 28
_HEIGHT = 28
_NCHANNELS = 1

_NUM_CLASSES = 10
_HIDDEN_LAYERS = 2
_HIDDEN_SIZE = 256

# resources names
repository_name = 'repository'
model_name = 'model'

sgd_optimizer_name = 'sgd'
adam_optimizer_name = 'adam'

criterion_name = 'cross_entropy_loss'
metricset_name = 'metricset'

benchmark_name = 'benchmark'  # todo!
naive_strategy_name = 'naive_strategy'
si_strategy_name = 'si_strategy'
lwf_strategy_name = 'lwf_strategy'
cumulative_strategy_name = 'cumulative_strategy'
replay_strategy_name = 'replay_strategy'

naive_experiment_name = 'naive_experiment'
cumulative_experiment_name = 'cumulative_experiment'
si_experiment_name = 'si_experiment'
lwf_experiment_name = 'lwf_experiment'
replay_experiment_name = 'replay_experiment'

# benchmarks builds
file_benchmark_build = {
    'name': "FileBasedClassificationBenchmark",
    'data_repository': repository_name,
    'img_type': 'greyscale',
    'train_stream': [
        [
            {
                'root': 'fashion_mnist/train/0',
                'all': True,
            },
            {
                'root': 'fashion_mnist/train/1',
                'all': True,
            }
        ],
        [
            {
                'root': 'fashion_mnist/train/2',
                'all': True,
            },
            {
                'root': 'fashion_mnist/train/3',
                'all': True,
            }
        ],
        [
            {
                'root': 'fashion_mnist/train/4',
                'all': True,
            },
            {
                'root': 'fashion_mnist/train/5',
                'all': True,
            }
        ],
        [
            {
                'root': 'fashion_mnist/train/6',
                'all': True,
            },
            {
                'root': 'fashion_mnist/train/7',
                'all': True,
            }
        ],
        [
            {
                'root': 'fashion_mnist/train/8',
                'all': True,
            },
            {
                'root': 'fashion_mnist/train/9',
                'all': True,
            }
        ],
    ],
    'test_stream': [
        [
            {
                'root': 'fashion_mnist/test/0',
                'all': True,
            },
            {
                'root': 'fashion_mnist/test/1',
                'all': True,
            }
        ],
        [
            {
                'root': 'fashion_mnist/test/2',
                'all': True,
            },
            {
                'root': 'fashion_mnist/test/3',
                'all': True,
            }
        ],
        [
            {
                'root': 'fashion_mnist/test/4',
                'all': True,
            },
            {
                'root': 'fashion_mnist/test/5',
                'all': True,
            }
        ],
        [
            {
                'root': 'fashion_mnist/test/6',
                'all': True,
            },
            {
                'root': 'fashion_mnist/test/7',
                'all': True,
            }
        ],
        [
            {
                'root': 'fashion_mnist/test/8',
                'all': True,
            },
            {
                'root': 'fashion_mnist/test/9',
                'all': True,
            }
        ],
    ],
    'other_streams': {
        'stream1': [
            [
                {
                    'root': 'fashion_mnist/test/0',
                    'all': True,
                }
            ],
            [
                {
                    'root': 'fashion_mnist/test/1',
                    'all': True,
                }
            ],
            [
                {
                    'root': 'fashion_mnist/test/2',
                    'all': True,
                }
            ],
            [
                {
                    'root': 'fashion_mnist/test/3',
                    'all': True,
                }
            ],
            [
                {
                    'root': 'fashion_mnist/test/4',
                    'all': True,
                }
            ],
        ]
    },
    'train_transform': {
        'name': 'TrainMNIST',
    },
    'eval_transform': {
        'name': 'EvalMNIST',
    },
    'other_transform_groups': {
        'stream1': {
            'item': {
                'name': 'TrainMNIST',
            },
            'target': {
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
            }
        }
    }
}

split_mnist_benchmark_build = {
    'name': 'SplitMNIST',
    'n_experiences': 5,
    'shuffle': True,
    'fixed_class_order': list(range(10)),
    'return_task_id': True,
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
    'eval_transform': {
        'name': 'EvalMNIST',
    }
}

split_fashion_mnist_benchmark_build = {
    'name': 'FashionMNIST',
    'n_experiences': 5,
    'shuffle': True,
    'train_transform': {
        'name': 'TrainMNIST',
    },
    'eval_transform': {
        'name': 'EvalMNIST',
    }
}

permuted_mnist_benchmark_build = {
    'name': 'PermutedMNIST',
    'n_experiences': 5,
    'train_transform': {
        'name': 'TrainMNIST',
    },
    'eval_transform': {
        'name': 'EvalMNIST',
    },
}

split_cifar10_benchmark_build = {
    'name': 'SplitCIFAR10',
    'n_experiences': 10,
    'return_task_id': True,
    'train_transform': {
        'name': 'TrainCIFAR10',
    },
    'eval_transform': {
        'name': 'EvalCIFAR10',
    }
}

split_cifar100_benchmark_build = {
    'name': 'SplitCIFAR100',
    'n_experiences': 10,
    'return_task_id': True,
    'train_transform': {
        'name': 'TrainCIFAR100',
    },
    'eval_transform': {
        'name': 'EvalCIFAR100',
    }
}

core50_ni_benchmark_build = {
    'name': 'CORe50',
    'scenario': 'ni',
    'mini': True,
    'train_transform': {
        'name': 'TrainCORe50',
    },
    'eval_transform': {
        'name': 'EvalCORe50',
    },
}

core50_nc_benchmark_build = {
    'name': 'CORe50',
    'scenario': 'nc',
    'mini': True,
    'train_transform': {
        'name': 'TrainCORe50',
    },
    'eval_transform': {
        'name': 'EvalCORe50',
    },
}

core50_nic_benchmark_build = {
    'name': 'CORe50',
    'scenario': 'nic',
    'mini': True,
    'train_transform': {
        'name': 'TrainCORe50',
    },
    'eval_transform': {
        'name': 'EvalCORe50',
    },
}

core50_nicv2_79_benchmark_build = {
    'name': 'CORe50',
    'scenario': 'nicv2_79',
    'mini': True,
    'train_transform': {
        'name': 'TrainCORe50',
    },
    'eval_transform': {
        'name': 'EvalCORe50',
    },
}

core50_nicv2_196_benchmark_build = {
    'name': 'CORe50',
    'scenario': 'nicv2_196',
    'mini': True,
    'train_transform': {
        'name': 'TrainCORe50',
    },
    'eval_transform': {
        'name': 'EvalCORe50',
    },
}

core50_nicv2_391_benchmark_build = {
    'name': 'CORe50',
    'scenario': 'nicv2_391',
    'mini': True,
    'train_transform': {
        'name': 'TrainCORe50',
    },
    'eval_transform': {
        'name': 'EvalCORe50',
    },
}

split_tiny_imagenet_benchmark_build = {
    'name': 'SplitTinyImageNet',
    'n_experiences': 10,
    'shuffle': True,
    'fixed_class_order': list(range(200)),
    'return_task_id': True,
    'train_transform': {
        'name': 'TrainTinyImageNet',
    },
    'eval_transform': {
        'name': 'EvalTinyImageNet',
    },
}

benchmark_build = file_benchmark_build  # split_mnist_benchmark_build todo!

# metricsets
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

# criterions
criterion_build = {
    'name': 'CrossEntropyLoss',
}

# optimizers
sgd_optimizer_build = {
    'name': 'SGD',
    'model': model_name,
    'learning_rate': 0.001,
    'momentum': 0.9,
}

adam_optimizer_build = {
    'name': 'Adam',
    'learning_rate': 0.001,
    'model': model_name,
}

# models
simple_mlp_build = {
    'name': 'SimpleMLP',
    'num_classes': _NUM_CLASSES,
    'input_size': _NCHANNELS * _WIDTH * _HEIGHT,
    'hidden_layers': _HIDDEN_LAYERS,
}

multihead_mlp_build = {
    'name': 'MultiHeadMLP',
    'input_size': _NCHANNELS * _WIDTH * _HEIGHT,
    'hidden_layers': _HIDDEN_LAYERS,
}

model_build = multihead_mlp_build # todo!

# strategies
naive_strategy_build = {
    'name': 'Naive',
    'model': model_name,
    'optimizer': adam_optimizer_name,
    'criterion': criterion_name,
    'metricset': metricset_name,

    'train_mb_size': _TRAIN_MB_SIZE,
    'train_epochs': _TRAIN_EPOCHS,
    'eval_mb_size': _EVAL_MB_SIZE,
}

cumulative_strategy_build = {
    'name': 'Cumulative',
    'model': model_name,
    'optimizer': adam_optimizer_name,
    'criterion': criterion_name,
    'metricset': metricset_name,

    'train_mb_size': _TRAIN_MB_SIZE,
    'train_epochs': _TRAIN_EPOCHS,
    'eval_mb_size': _EVAL_MB_SIZE,
}

si_strategy_build = {
    'name': 'SynapticIntelligence',
    'model': model_name,
    'optimizer': adam_optimizer_name,
    'criterion': criterion_name,
    'metricset': metricset_name,

    'train_mb_size': _TRAIN_MB_SIZE,
    'train_epochs': _TRAIN_EPOCHS,
    'eval_mb_size': _EVAL_MB_SIZE,

    'si_lambda': [1.0],
    'eps': 0.001,
}

lwf_strategy_build = {
    'name': 'LwF',
    'model': model_name,
    'optimizer': adam_optimizer_name,
    'criterion': criterion_name,
    'metricset': metricset_name,

    'train_mb_size': _TRAIN_MB_SIZE,
    'train_epochs': _TRAIN_EPOCHS,
    'eval_mb_size': _EVAL_MB_SIZE,

    'alpha': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
    'temperature': 1.0,
}

replay_strategy_build = {
    'name': 'Replay',
    'model': model_name,
    'optimizer': adam_optimizer_name,
    'criterion': criterion_name,
    'metricset': metricset_name,

    'train_mb_size': _TRAIN_MB_SIZE,
    'train_epochs': _TRAIN_EPOCHS,
    'eval_mb_size': _EVAL_MB_SIZE,

    'memory': 200,
}

# experiments
naive_experiment_build = {
    'name': 'ExperimentBuild',
    'strategy': naive_strategy_name,
    'benchmark': benchmark_name,
}

cumulative_experiment_build = {
    'name': 'ExperimentBuild',
    'strategy': cumulative_strategy_name,
    'benchmark': benchmark_name,
}

si_experiment_build = {
    'name': 'ExperimentBuild',
    'strategy': si_strategy_name,
    'benchmark': benchmark_name,
}

lwf_experiment_build = {
    'name': 'ExperimentBuild',
    'strategy': lwf_strategy_name,
    'benchmark': benchmark_name,
}

replay_experiment_build = {
    'name': 'ExperimentBuild',
    'strategy': replay_strategy_name,
    'benchmark': benchmark_name,
}


_TEST_ITEMS_PER_CATEGORY = 8
_TRAIN_ITEMS_PER_CATEGORY = 10 * _TEST_ITEMS_PER_CATEGORY




class ResourcesShellTest(BaseShellTest):

    repository_name = 'repository'
    repository = None

    benchmark = None
    criterion = None
    metricset = None
    model = None
    optimizer = None
    strategy = None

    def test_resources_creation_build(self):
        self.assertTrue(self.create_user_workspace())

        self.assertTrue(self.delete_user_workspace())


if __name__ == '__main__':
    unittest.main(verbosity=2)