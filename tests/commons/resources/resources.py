"""
Testing on base users and workspaces operations.
"""
from __future__ import annotations
import unittest

from client import *

from tests.utils import *


# Benchmarks
benchmark_type = 'benchmark'
benchmark_name = 'benchmark'
benchmark_desc = '...'
benchmark_build = {
    'name': 'SplitMNIST',
    'n_experiences': 5,
    'seed': 0,
    'return_task_id': False,
    'train_transform': {
        'name': 'TrainMNIST',
    },
    'eval_transform': {
        'name': 'EvalMNIST',
    },
}
edited_benchmark = {
    'name': f'new_{benchmark_name}',
    'build': {
        'n_experiences': 10,
        'seed': 1,
    }
}


# Models
model_type = 'model'
model_name = 'model'
model_desc = '...'
model_build = {
    'name': 'SimpleMLP',
    'num_classes': 10,
}

edited_model = {
    'name': f'new_{model_name}',
    'build': {
        'num_classes': 5,
    }
}


# Criterions
criterion_type = 'criterion'
criterion_name = 'criterion'
criterion_desc = '...'
criterion_build = {
    'name': 'CrossEntropyLoss',
}
edited_criterion = {
    'name': f'new_{criterion_name}',
}


# MetricSets
metric_set_type = 'metric_set'
metric_set_name = 'metric_set'
metric_set_desc = '...'
metric_set_build = {
    'name': 'StandardMetricSet',
    'accuracy': {
        'epoch': True,
        'experience': True,
        'stream': True,
    }
}
edited_metric_set = {
    'name': f'new_{metric_set_name}',
}


# Optimizers
optimizer_type = 'optimizer'
optimizer_name = 'optimizer'
optimizer_desc = '...'
optimizer_build = {
    'name': 'SGD',
    'model': model_name,
    'learning_rate': 0.001,
    'momentum': 0.9,
}
edited_optimizer = {
    'name': f'new_{optimizer_name}',
    'build': {
        'momentum': 0.8,
    }
}


# Strategies
strategy_type = 'strategy'
strategy_name = 'strategy'
strategy_desc = '...'
strategy_build = {
    'name': 'Naive',
    'model': model_name,
    'optimizer': optimizer_name,
    'criterion': criterion_name,
    'metricset': metric_set_name,

    'train_mb_size': 32,
    'train_epochs': 4,
    'eval_mb_size': 16,
}

edited_strategy = {
    'name': f'new_{strategy_name}',
}


class ResourceTestCase(BaseTestCase):
    """
    Base class for resources testing.
    """
    # Test parameters
    username = 'resource-username'
    email = f'resource_{EMAIL}'
    workspace = 'resource_workspace'
    password = PASSWORD
    host = HOST
    port = PORT
    client = BaseClient(host, port)
    deleted = False

    resources = ('metric_set', 'model', 'benchmark', 'criterion', 'optimizer', 'strategy')

    # "Macros"
    def register_login(self):
        # register
        self.assertBaseHandler(
            self.client.register(self.username, self.email, self.password), success_codes=HTTPStatus.CREATED,
        )

        # login
        self.assertBaseHandler(self.client.login(self.username, self.password))

    def create_workspace(self):
        # create workspace
        self.assertBaseHandler(self.client.create_workspace(self.workspace), success_codes=HTTPStatus.CREATED)

    def close_and_delete_workspace(self):
        # close workspace
        self.assertBaseHandler(self.client.close_workspace())

        # delete workspace
        self.assertBaseHandler(self.client.delete_workspace())

    def delete_user(self):
        # delete user
        self.assertBaseHandler(self.client.delete_user())
        self.deleted = True

    def handle_resource(self, resource_type, resource_name, resource_desc,
                        resource_build, edited_resource):
        create_method = eval(f"self.client.create_{resource_type}")
        get_method = eval(f"self.client.get_{resource_type}")
        rename_method = eval(f"self.client.rename_{resource_type}")
        update_method = eval(f"self.client.update_{resource_type}")

        # create, get, update, delete resource
        self.assertBaseHandler(create_method(
            name=resource_name, description=resource_desc, build_config_data=resource_build,
        ), success_codes=HTTPStatus.CREATED)

        self.assertBaseHandler(get_method(name=resource_name))

        self.assertBaseHandler(
            update_method(name=resource_name, updata=edited_resource),
            success_codes=[HTTPStatus.OK, HTTPStatus.NOT_MODIFIED],
        )

        self.assertBaseHandler(rename_method(name=f"new_{resource_name}", new_name=resource_name))

    def test_main(self):
        self.deleted = False
        with self.client.session(self.username, self.workspace):
            try:
                # register and login
                self.register_login()

                # create workspace
                self.create_workspace()

                for tp in self.resources:
                    resource_type = tp
                    resource_name = tp
                    resource_desc = '...'
                    resource_build = eval(f"{tp}_build")
                    edited_resource = eval(f"edited_{tp}")

                    # create, get, update, rename, delete resource
                    self.handle_resource(resource_type, resource_name, resource_desc,
                                         resource_build, edited_resource)

                for tp in self.resources[::-1]:
                    delete_method = eval(f"self.client.delete_{tp}")
                    self.assertBaseHandler(delete_method(name=tp))

                # close and delete workspace
                self.close_and_delete_workspace()

                # delete user
                self.delete_user()
            finally:
                if not self.deleted:
                    # delete user data anyway
                    self.client.close_workspace(self.workspace)
                    self.client.delete_workspace(self.workspace)
                    self.client.delete_user()
                    self.deleted = True


if __name__ == '__main__':
    unittest.main()