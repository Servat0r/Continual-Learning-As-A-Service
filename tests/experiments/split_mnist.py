from __future__ import annotations

import os
from time import sleep
import unittest

from client import *

from tests.utils import *

_TRAIN_MB_SIZE = 30
_TRAIN_EPOCHS = 2
_EVAL_MB_SIZE = 30

base_csv_folder = 'csv_results'

# resources names
benchmark_name = 'benchmark'
model_name = 'model'
optimizer_name = 'sgd'
criterion_name = 'cross_entropy_loss'
metricset_name = 'metricset'

naive_strategy_name = 'naive_strategy'
cumulative_strategy_name = 'cumulative_strategy'
gdumb_strategy_name = 'gdumb_strategy'
lwf_strategy_name = 'lwf_strategy'


naive_experiment_name = 'naive_experiment'
cumulative_experiment_name = 'cumulative_experiment'
gdumb_experiment_name = 'gdumb_experiment'
lwf_experiment_name = 'lwf_experiment'


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

model_build = {
    'name': 'SimpleMLP',
    'num_classes': 10,
    'input_size': 1 * 28 * 28,
    'hidden_layers': 2,
    'hidden_size': 512,
}

criterion_build = {
    'name': 'CrossEntropyLoss',
}

optimizer_build = {
    'name': 'SGD',
    'model': model_name,
    'learning_rate': 0.001,
    'momentum': 0.9,
}

naive_strategy_build = {
    'name': 'Naive',
    'model': model_name,
    'optimizer': optimizer_name,
    'criterion': criterion_name,
    'metricset': metricset_name,

    'train_mb_size': _TRAIN_MB_SIZE,
    'train_epochs': _TRAIN_EPOCHS,
    'eval_mb_size': _EVAL_MB_SIZE,
}

cumulative_strategy_build = {
    'name': 'Cumulative',
    'model': model_name,
    'optimizer': optimizer_name,
    'criterion': criterion_name,
    'metricset': metricset_name,

    'train_mb_size': _TRAIN_MB_SIZE,
    'train_epochs': _TRAIN_EPOCHS,
    'eval_mb_size': _EVAL_MB_SIZE,
}

gdumb_strategy_build = {
    'name': 'GDumb',
    'model': model_name,
    'optimizer': optimizer_name,
    'criterion': criterion_name,
    'metricset': metricset_name,

    'train_mb_size': _TRAIN_MB_SIZE,
    'train_epochs': _TRAIN_EPOCHS,
    'eval_mb_size': _EVAL_MB_SIZE,

    'memory': 500,
}

lwf_strategy_build = {
    'name': 'LwF',
    'model': model_name,
    'optimizer': optimizer_name,
    'criterion': criterion_name,
    'metricset': metricset_name,

    'train_mb_size': _TRAIN_MB_SIZE,
    'train_epochs': _TRAIN_EPOCHS,
    'eval_mb_size': _EVAL_MB_SIZE,

    'alpha': [1.0, 1.0, 1.0, 1.0, 1.0],
    'temperature': 1.0,
}

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

gdumb_experiment_build = {
    'name': 'ExperimentBuild',
    'strategy': gdumb_strategy_name,
    'benchmark': benchmark_name,
}

lwf_experiment_build = {
    'name': 'ExperimentBuild',
    'strategy': lwf_strategy_name,
    'benchmark': benchmark_name,
}


class SplitMNISTTest(BaseTestCase):

    username = 'split-mnist-username'
    email = EMAIL
    password = PASSWORD
    workspace = 'split_mnist_workspace'
    host = HOST
    port = PORT
    client = BaseClient(host, port)

    base_folder = os.path.join(base_csv_folder, 'split_mnist')
    
    model_name = model_name
    model_build = model_build
    
    optimizer_name = optimizer_name
    optimizer_build = optimizer_build
    
    criterion_name = criterion_name
    criterion_build = criterion_build
    
    metricset_name = metricset_name
    metricset_build = metricset_build
    
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
            'folder': 'gdumb',
            'strategy_name': gdumb_strategy_name,
            'strategy_build': gdumb_strategy_build,
            'experiment_name': gdumb_experiment_name,
            'experiment_build': gdumb_experiment_build,
        },
        {
            'folder': 'lwf',
            'strategy_name': lwf_strategy_name,
            'strategy_build': lwf_strategy_build,
            'experiment_name': lwf_experiment_name,
            'experiment_build': lwf_experiment_build,
        },
    ]
    
    def setUp(self) -> None:
        super().setUp()
        os.makedirs(self.base_folder, exist_ok=True)
    
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
            self.assertBaseHandler(self.client.create_benchmark(benchmark_name, benchmark_build))
            
            self.assertBaseHandler(self.client.create_metric_set(metricset_name, metricset_build))
            
            self.assertBaseHandler(self.client.create_model(model_name, model_build))
            
            self.assertBaseHandler(self.client.create_optimizer(optimizer_name, optimizer_build))
            
            self.assertBaseHandler(self.client.create_criterion(criterion_name, criterion_build))
            
            # strategies and experiments creation
            for descriptor in self.experiment_data:
                folder = descriptor['folder']
                strategy_name = descriptor['strategy_name']
                strategy_build = descriptor['strategy_build']

                experiment_name = descriptor['experiment_name']
                experiment_build = descriptor['experiment_build']

                base_exp_dir = os.path.join(self.base_folder, folder)
                os.makedirs(base_exp_dir, exist_ok=True)
                self.assertBaseHandler(self.client.create_strategy(strategy_name, strategy_build))
                self.assertBaseHandler(self.client.create_experiment(experiment_name, experiment_build))
                self.assertBaseHandler(self.client.setup_experiment(experiment_name))
                self.assertBaseHandler(self.client.start_experiment(experiment_name))

                # noinspection PyUnusedLocal
                ok = False
                while True:
                    sleep(6)
                    response = self.client.get_experiment_results(experiment_name)
                    base_response_handler(response)
                    if response.status_code == HTTPStatus.OK:
                        ok = True
                        break

                if ok:
                    response = self.client.get_experiment_csv_results(experiment_name)
                    if response.status_code == HTTPStatus.OK:
                        data = response.json()
                        train_csv = data.get('train', '')
                        eval_csv = data.get('eval', '')

                        with open(os.path.join(base_exp_dir, 'train_results.csv'), 'w') as f:
                            f.write(train_csv)
                        with open(os.path.join(base_exp_dir, 'eval_results.csv'), 'w') as f:
                            f.write(eval_csv)
            
            # close workspace
            self.assertBaseHandler(self.client.close_workspace())

            # delete workspace
            self.assertBaseHandler(self.client.delete_workspace())

            # delete user
            self.assertBaseHandler(self.client.delete_user())


if __name__ == '__main__':
    unittest.main(verbosity=2)