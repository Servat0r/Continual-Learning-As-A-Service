from __future__ import annotations

from application.utils import TBoolStr, t, TDesc, abstractmethod, get_common_dataset_root
from application.database import db

from application.resources.contexts import ResourceContext
from application.resources.base import DataType

from application.mongo.data_managing import MongoDataRepository
from application.mongo.resources.mongo_base_configs import *


class MongoBaseBenchmarkBuildConfig(MongoBuildConfig):

    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    data_repository = db.ReferenceField(MongoDataRepository, default=None)

    @classmethod
    @abstractmethod
    def get_required(cls) -> set[str]:
        return set()

    @classmethod
    @abstractmethod
    def get_optionals(cls) -> set[str]:
        return {'data_repository'}

    @classmethod
    @abstractmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        return super(MongoBaseBenchmarkBuildConfig, cls).validate_input(data, dtype, context)

    @classmethod
    @abstractmethod
    def create(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super(MongoBaseBenchmarkBuildConfig, cls).create(data, dtype, context, save)

    @abstractmethod
    def build(self, context: ResourceContext, locked=False, parents_locked=False):
        return super(MongoBaseBenchmarkBuildConfig, self).build(context, locked, parents_locked)

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type('Benchmark')


class MongoBaseClassicBenchmarkBuildConfig(MongoBaseBenchmarkBuildConfig):

    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    n_experiences = db.IntField(required=True)
    return_task_id = db.BooleanField(default=False)
    seed = db.IntField(default=None)
    fixed_class_order = db.ListField(db.IntField(), default=None)
    shuffle = db.BooleanField(default=True)

    @staticmethod
    @abstractmethod
    def benchmark_generator() -> t.Callable:
        pass

    @staticmethod
    @abstractmethod
    def dataset_name() -> str:
        pass

    @classmethod
    def get_required(cls) -> set[str]:
        return {'n_experiences'}

    @classmethod
    def get_optionals(cls) -> set[str]:
        return {
            'data_repository',
            'return_task_id',
            'seed',
            'fixed_class_order',
            'shuffle',
        }

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        result, msg = super(MongoBaseClassicBenchmarkBuildConfig, cls).validate_input(data, dtype, context)
        if not result:
            return result, msg
        iname, values = context.pop()
        params: TDesc = values['params']

        n_experiences = params['n_experiences']
        seed = params.get('seed', 0)
        all_int = all(isinstance(val, int) for val in [n_experiences, seed])

        return_task_id = params.get('return_task_id', False)
        shuffle = params.get('shuffle', True)
        all_bool = all(isinstance(val, bool) for val in [return_task_id, shuffle])

        checked_class_order = True
        fixed_class_order = params.get('fixed_class_order')
        if fixed_class_order is not None:
            checked_class_order = isinstance(fixed_class_order, list)
            if checked_class_order:
                checked_class_order = all(isinstance(item, int) for item in fixed_class_order)

        ok = all_int and all_bool and checked_class_order
        if not ok:
            return False, "One or more parameters are not of the correct type!"
        context.push(iname, values)
        return True, None

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super(MongoBaseClassicBenchmarkBuildConfig, cls).create(data, tp, context, save)

    def build(self, context: ResourceContext, locked=False, parents_locked=False):
        dataset_root = get_common_dataset_root(self.dataset_name(), abspath=True)
        benchmark = self.benchmark_generator()(
            self.n_experiences,
            return_task_id=self.return_task_id,
            seed=self.seed,
            fixed_class_order=self.fixed_class_order,
            shuffle=self.shuffle,
            dataset_root=dataset_root,
        )
        # noinspection PyArgumentList
        return self.target_type()(benchmark)


__all__ = [
    'MongoBaseBenchmarkBuildConfig',
    'MongoBaseClassicBenchmarkBuildConfig',
]