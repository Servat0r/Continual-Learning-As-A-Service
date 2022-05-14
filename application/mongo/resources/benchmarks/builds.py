from __future__ import annotations
from avalanche.benchmarks.classic import SplitMNIST

from application.utils import TBoolStr, t, TDesc
from application.database import db

from application.resources.contexts import ResourceContext
from application.resources.base import DataType

from application.mongo.resources.mongo_base_configs import *
from .base_builds import *


# SplitMNIST builder
@MongoBuildConfig.register_build_config('SplitMNIST')
class SplitMNISTBuildConfig(MongoBaseBenchmarkBuildConfig):
    """
    Build config for a standard SplitMNIST benchmark based on avalanche.benchmarks.classics#SplitMNIST function.
    """
    n_experiences = db.IntField(required=True)
    return_task_id = db.BooleanField(required=False, default=False)
    seed = db.IntField(default=None)
    fixed_class_order = db.ListField(db.IntField(), default=None)
    shuffle = db.BooleanField(default=True)
    dataset_root = db.StringField(default=None)

    @classmethod
    def get_required(cls) -> set[str]:
        return {'n_experiences'}

    @classmethod
    def get_optionals(cls) -> set[str]:
        return {
            'return_task_id',
            'seed',
            'fixed_class_order',
            'shuffle',
            'dataset_root',
        }

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type('Benchmark')

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        result, msg = super().validate_input(data, dtype, context)
        if not result:
            return result, msg
        _, values = context.head()
        params = values['params']
        result = all(isinstance(val, int) for val in params.values())
        if not result:
            context.pop()
        return result, None if result else "One or more parameter(s) is/are incorrect."

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super().create(data, tp, context, save)

    def build(self, context: ResourceContext, locked=False, parents_locked=False):
        benchmark = SplitMNIST(
            self.n_experiences,
            return_task_id=self.return_task_id,
            seed=self.seed,
            fixed_class_order=self.fixed_class_order,
            shuffle=self.shuffle,
            dataset_root=self.dataset_root,
        )
        # noinspection PyArgumentList
        return self.target_type()(benchmark)


# FashionMNIST builder


# PathsDataset builder
@MongoBuildConfig.register_build_config('PathsBenchmark')
class PathsBenchmarkBuildConfig(MongoBaseBenchmarkBuildConfig):
    """
    This build config models a benchmark built starting from
    a set of data in a data repository, similarly to what
    happens for paths_benchmark.
    The configuration has the following syntax:
    {
        "name": "PathsBenchmark",
        "data_repository": <data_repository_name>,
        "streams": {    # Benchmark streams
            "train": [  # train stream
                {
                    "root": <root_path>   # (within the data repository; if not given, it is intended as data repo root)
                    "all": true/false   # if true, loads all files in the data repo; otherwise, loads the given ones;
                    "files": [          # list of file paths (relative to root) to load;
                        <path>,
                        <path>,
                        ...
                    ]
                }
            ],
            "test" [    # test stream
                ...
            ],
            ...         # other streams
        }

    }
    """

    ...


__all__ = [
    'SplitMNISTBuildConfig',
]