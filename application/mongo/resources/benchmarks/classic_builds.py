from __future__ import annotations
from avalanche.benchmarks.classic import SplitMNIST, SplitFMNIST, PermutedMNIST, \
    SplitCIFAR10, SplitCIFAR100, CORe50, SplitTinyImageNet

from application.utils import TBoolStr, t, TDesc, get_common_dataset_root
from application.database import db

from application.resources.contexts import ResourceContext
from application.resources.base import DataType

from application.mongo.resources.mongo_base_configs import *
from .base_builds import *


# SplitMNIST builder
@MongoBuildConfig.register_build_config('SplitMNIST')
class SplitMNISTBuildConfig(MongoBaseClassicBenchmarkBuildConfig):
    """
    Build config for a standard SplitMNIST benchmark based on avalanche.benchmarks.classics#SplitMNIST function.
    """
    @staticmethod
    def benchmark_generator() -> t.Callable:
        return SplitMNIST

    @staticmethod
    def dataset_name() -> str:
        return 'mnist'

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        result, msg = super(SplitMNISTBuildConfig, cls).validate_input(data, dtype, context)
        if result:
            context.pop()
        return result, msg


# SplitFashionMNIST builder
@MongoBuildConfig.register_build_config('SplitFashionMNIST')
class SplitFashionMNISTBuildConfig(MongoBaseClassicBenchmarkBuildConfig):

    # Fields
    first_batch_with_half_classes = db.BooleanField(required=False, default=False)

    @staticmethod
    def benchmark_generator() -> t.Callable:
        return SplitFMNIST

    @staticmethod
    def dataset_name() -> str:
        return 'mnist'

    @classmethod
    def get_required(cls) -> set[str]:
        return super(SplitFashionMNISTBuildConfig, cls).get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(SplitFashionMNISTBuildConfig, cls).get_optionals().union({'first_batch_with_half_classes'})

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        result, msg = super(SplitFashionMNISTBuildConfig, cls).validate_input(data, dtype, context)
        if not result:
            return result, msg
        iname, values = context.pop()
        params: TDesc = values['params']

        n_experiences = params['n_experiences']
        seed = params.get('seed', 0)
        all_int = all(isinstance(val, int) for val in [n_experiences, seed])

        first_batch_with_half_classes = params.get('first_batch_with_half_classes', False)
        return_task_id = params.get('return_task_id', False)
        shuffle = params.get('shuffle', True)
        all_bool = all(isinstance(val, bool) for val in [first_batch_with_half_classes, return_task_id, shuffle])

        checked_class_order = True
        fixed_class_order = params.get('fixed_class_order')
        if fixed_class_order is not None:
            checked_class_order = isinstance(fixed_class_order, list)
            if checked_class_order:
                checked_class_order = all(isinstance(item, int) for item in fixed_class_order)

        ok = all_int and all_bool and checked_class_order
        if not ok:
            return False, "One or more parameters are not of the correct type!"
        return True, None

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super(SplitFashionMNISTBuildConfig, cls).create(data, tp, context, save)

    def build(self, context: ResourceContext, locked=False, parents_locked=False):
        dataset_root = get_common_dataset_root(self.dataset_name(), abspath=True)
        benchmark = self.benchmark_generator()(
            self.n_experiences,
            first_batch_with_half_classes=self.first_batch_with_half_classes,
            return_task_id=self.return_task_id,
            seed=self.seed,
            fixed_class_order=self.fixed_class_order,
            shuffle=self.shuffle,
            dataset_root=dataset_root,
        )
        # noinspection PyArgumentList
        return self.target_type()(benchmark)


# PermutedMNIST builder
@MongoBuildConfig.register_build_config('PermutedMNIST')
class PermutedMNISTBuildConfig(MongoBaseBenchmarkBuildConfig):

    # Fields
    n_experiences = db.IntField(required=True)
    seed = db.IntField(default=None)

    @classmethod
    def get_required(cls) -> set[str]:
        return super(PermutedMNISTBuildConfig, cls).get_required().union({'n_experiences'})

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(PermutedMNISTBuildConfig, cls).get_optionals().union({'seed', 'dataset_root'})

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        result, msg = super(PermutedMNISTBuildConfig, cls).validate_input(data, dtype, context)
        if not result:
            return result, msg
        iname, values = context.pop()
        params: TDesc = values['params']

        n_experiences = params['n_experiences']
        seed = params.get('seed', 0)
        all_int = all(isinstance(val, int) for val in [n_experiences, seed])

        if not all_int:
            return False, "One or more parameters are not of the correct type!"
        return True, None

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super(PermutedMNISTBuildConfig, cls).create(data, tp, context, save)

    def build(self, context: ResourceContext, locked=False, parents_locked=False):
        dataset_root = get_common_dataset_root('mnist', abspath=True)
        benchmark = PermutedMNIST(
            self.n_experiences,
            seed=self.seed,
            dataset_root=dataset_root,
        )
        # noinspection PyArgumentList
        return self.target_type()(benchmark)


# Split CIFAR-10 builder
@MongoBuildConfig.register_build_config('SplitCIFAR10')
class SplitCIFAR10BuildConfig(MongoBaseClassicBenchmarkBuildConfig):
    
    # Fields
    first_exp_with_half_classes = db.BooleanField(default=False)
    
    @staticmethod
    def benchmark_generator() -> t.Callable:
        return SplitCIFAR10
    
    @staticmethod
    def dataset_name() -> str:
        return 'cifar10'

    @classmethod
    def get_required(cls) -> set[str]:
        return super(SplitCIFAR10BuildConfig, cls).get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(SplitCIFAR10BuildConfig, cls).get_optionals().union({'first_exp_with_half_classes'})

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        result, msg = super(SplitCIFAR10BuildConfig, cls).validate_input(data, dtype, context)
        if not result:
            return result, msg
        iname, values = context.pop()
        params: TDesc = values['params']

        n_experiences = params['n_experiences']
        seed = params.get('seed', 0)
        all_int = all(isinstance(val, int) for val in [n_experiences, seed])

        first_exp_with_half_classes = params.get('first_exp_with_half_classes', False)
        return_task_id = params.get('return_task_id', False)
        shuffle = params.get('shuffle', True)
        all_bool = all(isinstance(val, bool) for val in [first_exp_with_half_classes, return_task_id, shuffle])

        checked_class_order = True
        fixed_class_order = params.get('fixed_class_order')
        if fixed_class_order is not None:
            checked_class_order = isinstance(fixed_class_order, list)
            if checked_class_order:
                checked_class_order = all(isinstance(item, int) for item in fixed_class_order)

        ok = all_int and all_bool and checked_class_order
        if not ok:
            return False, "One or more parameters are not of the correct type!"
        return True, None

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super(SplitCIFAR10BuildConfig, cls).create(data, tp, context, save)

    def build(self, context: ResourceContext, locked=False, parents_locked=False):
        dataset_root = get_common_dataset_root(self.dataset_name(), abspath=True)
        benchmark = self.benchmark_generator()(
            self.n_experiences,
            first_exp_with_half_classes=self.first_exp_with_half_classes,
            return_task_id=self.return_task_id,
            seed=self.seed,
            fixed_class_order=self.fixed_class_order,
            shuffle=self.shuffle,
            dataset_root=dataset_root,
        )
        # noinspection PyArgumentList
        return self.target_type()(benchmark)


# Split CIFAR-100 builder
@MongoBuildConfig.register_build_config('SplitCIFAR100')
class SplitCIFAR100BuildConfig(MongoBaseClassicBenchmarkBuildConfig):

    # Fields
    first_exp_with_half_classes = db.BooleanField(default=False)

    @staticmethod
    def benchmark_generator() -> t.Callable:
        return SplitCIFAR100

    @staticmethod
    def dataset_name() -> str:
        return 'cifar100'

    @classmethod
    def get_required(cls) -> set[str]:
        return super(SplitCIFAR100BuildConfig, cls).get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(SplitCIFAR100BuildConfig, cls).get_optionals().union({'first_exp_with_half_classes'})

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        result, msg = super(SplitCIFAR100BuildConfig, cls).validate_input(data, dtype, context)
        if not result:
            return result, msg
        iname, values = context.pop()
        params: TDesc = values['params']

        n_experiences = params['n_experiences']
        seed = params.get('seed', 0)
        all_int = all(isinstance(val, int) for val in [n_experiences, seed])

        first_exp_with_half_classes = params.get('first_exp_with_half_classes', False)
        return_task_id = params.get('return_task_id', False)
        shuffle = params.get('shuffle', True)
        all_bool = all(isinstance(val, bool) for val in [first_exp_with_half_classes, return_task_id, shuffle])

        checked_class_order = True
        fixed_class_order = params.get('fixed_class_order')
        if fixed_class_order is not None:
            checked_class_order = isinstance(fixed_class_order, list)
            if checked_class_order:
                checked_class_order = all(isinstance(item, int) for item in fixed_class_order)

        ok = all_int and all_bool and checked_class_order
        if not ok:
            return False, "One or more parameters are not of the correct type!"
        return True, None

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super(SplitCIFAR100BuildConfig, cls).create(data, tp, context, save)

    def build(self, context: ResourceContext, locked=False, parents_locked=False):
        dataset_root = get_common_dataset_root(self.dataset_name(), abspath=True)
        benchmark = self.benchmark_generator()(
            self.n_experiences,
            first_exp_with_half_classes=self.first_exp_with_half_classes,
            return_task_id=self.return_task_id,
            seed=self.seed,
            fixed_class_order=self.fixed_class_order,
            shuffle=self.shuffle,
            dataset_root=dataset_root,
        )
        # noinspection PyArgumentList
        return self.target_type()(benchmark)


# CORe50 builder
@MongoBuildConfig.register_build_config('CORe50')
class CORe50BuildConfig(MongoBaseBenchmarkBuildConfig):

    _NI = 'ni'
    _NC = 'nc'
    _NIC = 'nic'
    _NICV2_79 = 'nicv2_79'
    _NICV2_196 = 'nicv2_196'
    _NICV2_391 = 'nicv2_391'

    # Fields
    scenario = db.StringField(choices=(_NI, _NC, _NIC, _NICV2_79, _NICV2_196, _NICV2_391), default=_NICV2_391)
    run = db.IntField(default=0)
    object_lvl = db.BooleanField(default=True)
    mini = db.BooleanField(default=False)   # True -> 32x32 images; False -> 128x128 images

    @classmethod
    def get_required(cls) -> set[str]:
        return super(CORe50BuildConfig, cls).get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(CORe50BuildConfig, cls).get_optionals().union({
            'data_repository', 'scenario', 'run', 'object_lvl', 'mini'
        })

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        result, msg = super(CORe50BuildConfig, cls).validate_input(data, dtype, context)
        if not result:
            return result, msg
        iname, values = context.pop()
        params: TDesc = values['params']

        scenario = params.get('scenario', cls._NICV2_391)
        run = params.get('run', 0)
        object_lvl = params.get('object_lvl', True)
        mini = params.get('mini', False)

        all_bool = all(isinstance(val, bool) for val in [object_lvl, mini])
        all_int = all(isinstance(val, int) for val in [run]) and (0 <= run <= 9)
        all_str = all(isinstance(val, str) for val in [scenario])

        if not all_str and all_int and all_bool:
            return False, "One or more parameter(s) are not of the correct type!"
        return True, None

    @classmethod
    def create(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super(CORe50BuildConfig, cls).create(data, dtype, context, save)

    def build(self, context: ResourceContext, locked=False, parents_locked=False):
        dataset_root = get_common_dataset_root('core50', abspath=True)
        benchmark = CORe50(
            scenario=self.scenario,
            run=self.run,
            object_lvl=self.object_lvl,
            mini=self.mini,
            dataset_root=dataset_root,
        )
        # noinspection PyArgumentList
        return self.target_type()(benchmark)


# Split Tiny ImageNet builder
@MongoBuildConfig.register_build_config('SplitTinyImageNet')
class SplitTinyImageNetBuildConfig(MongoBaseClassicBenchmarkBuildConfig):

    @staticmethod
    def benchmark_generator() -> t.Callable:
        return SplitTinyImageNet

    @staticmethod
    def dataset_name() -> str:
        return 'tiny_imagenet'

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        result, msg = super(SplitTinyImageNetBuildConfig, cls).validate_input(data, dtype, context)
        if result:
            context.pop()
        return result, msg


__all__ = [
    # (Fashion)MNIST
    'SplitMNISTBuildConfig',
    'PermutedMNISTBuildConfig',
    'SplitFashionMNISTBuildConfig',

    # CIFAR
    'SplitCIFAR10BuildConfig',
    'SplitCIFAR100BuildConfig',

    # CORe50
    'CORe50BuildConfig',

    # (Tiny)ImageNet
    'SplitTinyImageNetBuildConfig',
]