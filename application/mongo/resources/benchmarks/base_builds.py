from __future__ import annotations

import schema as sch

from application.utils import TBoolStr, t, TDesc, abstractmethod, get_common_dataset_root
from application.database import db

from application.resources.contexts import ResourceContext
from application.resources.base import DataType

from application.mongo.data_managing import MongoDataRepository
from application.mongo.resources.mongo_base_configs import *

from .transform_builds import *


class MongoBaseBenchmarkBuildConfig(MongoBuildConfig):

    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    data_repository = db.ReferenceField(MongoDataRepository, default=None)

    @classmethod
    def schema_dict(cls) -> dict:
        result = super(MongoBaseBenchmarkBuildConfig, cls).schema_dict()
        result.update({
            sch.Optional('data_repository'): str,
        })
        return result

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

    @abstractmethod
    def to_dict(self, links=True) -> TDesc:
        data = {'data_repository': self.data_repository} if self.data_repository is not None else {}
        data.update(super().to_dict())
        return data


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
    train_transform = db.EmbeddedDocumentField(TransformConfig, default=None)
    eval_transform = db.EmbeddedDocumentField(TransformConfig, default=None)

    @classmethod
    def schema_dict(cls) -> dict:
        result = super(MongoBaseClassicBenchmarkBuildConfig, cls).schema_dict()
        result.update({
            'n_experiences': int,
            sch.Optional('return_task_id', default=False): bool,
            sch.Optional('seed', default=None): int,
            sch.Optional('fixed_class_order', default=None): [int],
            sch.Optional('shuffle', default=True): bool,
            sch.Optional('train_transform', default=None): {str: object},
            sch.Optional('eval_transform', default=None): {str: object},
        })
        return result

    @staticmethod
    @abstractmethod
    def default_train_transform() -> t.Type[TransformConfig]:
        pass

    @staticmethod
    @abstractmethod
    def default_eval_transform() -> t.Type[TransformConfig]:
        pass

    def extra_dict_data(self) -> TDesc:
        """
        Method used to add build config-specific fields to resource dict.
        MongoBaseClassicBenchmarkBuildConfig subclasses should redefine this method ONLY
        if they have extra fields or they want to include extra information.
        :return: A dictionary used for updating main representation dict in to_dict(...).
        """
        return {}

    def to_dict(self, links=True) -> TDesc:
        data = {
            'n_experiences': self.n_experiences,
            'return_task_id': self.return_task_id,
            'seed': self.seed,
            'fixed_class_order': self.fixed_class_order,
            'shuffle': self.shuffle,
        }
        if self.train_transform is not None:
            data['train_transform'] = self.train_transform.to_dict(links=False),
        if self.eval_transform is not None:
            data['eval_transform'] = self.eval_transform.to_dict(links=False),
        data.update(super().to_dict(links=links))
        extra = self.extra_dict_data()
        data.update(extra)
        return data

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
            'train_transform',
            'eval_transform',
        }

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        result, msg = super(MongoBaseClassicBenchmarkBuildConfig, cls).validate_input(data, dtype, context)
        if not result:
            return result, msg

        """
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
        train_transform_data = params.get('train_transform')
        eval_transform_data = params.get('eval_transform')
        """
        train_transform_data = data.get('train_transform')
        eval_transform_data = data.get('eval_transform')

        if train_transform_data is not None:
            train_transform_config: t.Type[TransformConfig] = TransformConfig.get_by_name(train_transform_data)
            if train_transform_data is None:
                return False, "Not given or unknown train transform."
            result, msg = train_transform_config.validate_input(train_transform_data, context)
            if not result:
                return False, f"Train transform is incorrect: '{msg}'."

        if eval_transform_data is not None:
            eval_transform_config: t.Type[TransformConfig] = TransformConfig.get_by_name(eval_transform_data)
            if eval_transform_data is None:
                return False, "Not given or unknown eval transform."
            result, msg = eval_transform_config.validate_input(eval_transform_data, context)
            if not result:
                return False, f"Eval transform is incorrect: '{msg}'."

        # context.push(iname, values)
        return True, None

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: ResourceContext, save: bool = True):
        train_transform_data = data.get('train_transform')
        if train_transform_data is not None:
            train_transform_config: t.Type[TransformConfig] = TransformConfig.get_by_name(train_transform_data)
            train_transform = train_transform_config.create(train_transform_data, context, save)
        else:
            train_transform = None
        data['train_transform'] = train_transform

        eval_transform_data = data.get('eval_transform')
        if eval_transform_data is not None:
            eval_transform_config: t.Type[TransformConfig] = TransformConfig.get_by_name(eval_transform_data)
            eval_transform = eval_transform_config.create(eval_transform_data, context, save)
        else:
            eval_transform = None
        data['eval_transform'] = eval_transform
        return super(MongoBaseClassicBenchmarkBuildConfig, cls).create(data, tp, context, save)

    def add_transforms(self, kwargs: TDesc):
        if self.train_transform is not None:
            train_transform = self.train_transform.get_transform()
            kwargs['train_transform'] = train_transform

        if self.eval_transform is not None:
            eval_transform = self.eval_transform.get_transform()
            kwargs['eval_transform'] = eval_transform

    def make_kwargs(self) -> TDesc:
        dataset_root = get_common_dataset_root(self.dataset_name(), abspath=True)
        kwargs = {
            'return_task_id': self.return_task_id,
            'seed': self.seed,
            'fixed_class_order': self.fixed_class_order,
            'shuffle': self.shuffle,
            'dataset_root': dataset_root,
        }
        self.add_transforms(kwargs)
        return kwargs

    def build(self, context: ResourceContext, locked=False, parents_locked=False):
        kwargs = self.make_kwargs()
        benchmark = self.benchmark_generator()(self.n_experiences, **kwargs)
        # noinspection PyArgumentList
        return self.target_type()(benchmark)


__all__ = [
    'MongoBaseBenchmarkBuildConfig',
    'MongoBaseClassicBenchmarkBuildConfig',
]