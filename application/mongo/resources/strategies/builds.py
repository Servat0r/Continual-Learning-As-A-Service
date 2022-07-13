from __future__ import annotations

import schema as sch

from avalanche.training.templates import SupervisedTemplate
from avalanche.training.supervised import Naive, Cumulative, JointTraining, \
    Replay, GDumb, SynapticIntelligence, LwF, EWC, CWRStar, AGEM

from application.utils import TBoolStr, t, TDesc, get_device
from application.database import db
from application.models import User, Workspace

from application.resources.contexts import UserWorkspaceResourceContext
from application.resources.base import DataType

from application.mongo.base import MongoBaseUser
from application.mongo.resources.mongo_base_configs import *
from .base_builds import *

from application.mongo.resources.metricsets import *
from application.mongo.resources.criterions import *
from application.mongo.resources.optimizers import *
from application.mongo.resources.models import *


# Naive strategy builder
@MongoBuildConfig.register_build_config('Naive')
class NaiveBuildConfig(MongoBaseStrategyBuildConfig):
    """
    Build config for Naive strategy.
    """
    def to_dict(self, links=True) -> TDesc:
        return super().to_dict(links=links)

    @staticmethod
    def get_avalanche_strategy() -> t.Type[SupervisedTemplate]:
        return Naive

    @classmethod
    def get_required(cls) -> set[str]:
        return super().get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super().get_optionals()

    def extra_build_params_process(self) -> TDesc:
        return {}

    @classmethod
    def extra_create_params_process(cls, params: TDesc) -> TDesc:
        return params


# Cumulative strategy builder
@MongoBuildConfig.register_build_config('Cumulative')
class CumulativeBuildConfig(MongoBaseStrategyBuildConfig):

    def to_dict(self, links=True) -> TDesc:
        return super().to_dict(links=links)

    @staticmethod
    def get_avalanche_strategy() -> t.Type[SupervisedTemplate]:
        return Cumulative

    @classmethod
    def get_required(cls) -> set[str]:
        return super().get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super().get_optionals()

    @classmethod
    def extra_create_params_process(cls, params: TDesc) -> TDesc:
        return params

    def extra_build_params_process(self) -> TDesc:
        return {}


# Joint Training
@MongoBuildConfig.register_build_config('JointTraining')
class JointTrainingBuildConfig(MongoBaseStrategyBuildConfig):

    def to_dict(self, links=True) -> TDesc:
        return super().to_dict(links=links)

    @staticmethod
    def get_avalanche_strategy() -> t.Type[SupervisedTemplate]:
        return JointTraining

    @classmethod
    def get_required(cls) -> set[str]:
        return super().get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super().get_optionals()

    @classmethod
    def extra_create_params_process(cls, params: TDesc) -> TDesc:
        return params

    def extra_build_params_process(self) -> TDesc:
        return {}


# Synaptic Intelligence strategy builder
@MongoBuildConfig.register_build_config('SynapticIntelligence')
class SynapticIntelligenceBuildConfig(MongoBaseStrategyBuildConfig):

    # Fields
    si_lambda = db.ListField(db.FloatField(), required=True)
    si_lambda_for_all = db.BooleanField(default=False)
    eps = db.FloatField(default=0.0000001)

    def to_dict(self, links=True) -> TDesc:
        data = super().to_dict(links=links)
        data.update({
            'si_lambda': self.si_lambda[0] if self.si_lambda_for_all else self.si_lambda,
            'eps': self.eps,
        })
        return data

    @classmethod
    def schema_dict(cls) -> dict:
        data = super().schema_dict()
        data.update({
            'si_lambda': sch.Or(float, [float]),
            sch.Optional('eps'): float,
        })
        return data

    @staticmethod
    def get_avalanche_strategy() -> t.Type[SupervisedTemplate]:
        return SynapticIntelligence

    @classmethod
    def get_required(cls) -> set[str]:
        return (super().get_required() or set()).union({'si_lambda'})

    @classmethod
    def get_optionals(cls) -> set[str]:
        return (super().get_optionals() or set()).union({'eps'})

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: UserWorkspaceResourceContext) -> TBoolStr:
        return super(SynapticIntelligenceBuildConfig, cls).validate_input(data, dtype, context)

    @classmethod
    def extra_create_params_process(cls, params: TDesc) -> TDesc:
        si_lambda = params['si_lambda']
        si_lambda_for_all = True if isinstance(si_lambda, float) else False
        si_lambda = [si_lambda] if si_lambda_for_all else si_lambda
        params['si_lambda'] = si_lambda
        params['si_lambda_for_all'] = si_lambda_for_all
        return params

    def extra_build_params_process(self) -> TDesc:
        si_lambda = self.si_lambda[0] if self.si_lambda_for_all else self.si_lambda
        return {'si_lambda': si_lambda, 'eps': self.eps}


# Learning without Forgetting
@MongoBuildConfig.register_build_config('LwF')
class LwFBuildConfig(MongoBaseStrategyBuildConfig):

    # Fields
    alpha = db.ListField(db.FloatField(), required=True)
    alpha_for_all = db.BooleanField(default=False)
    temperature = db.FloatField(required=True)

    def to_dict(self, links=True) -> TDesc:
        data = super().to_dict(links=links)
        data.update({
            'alpha': self.alpha[0] if self.alpha_for_all else self.alpha,
            'temperature': self.temperature,
        })
        return data

    @classmethod
    def schema_dict(cls) -> dict:
        data = super(LwFBuildConfig, cls).schema_dict()
        data.update({
            'alpha': sch.Or(float, [float]),
            'temperature': float,
        })
        return data

    @staticmethod
    def get_avalanche_strategy() -> t.Type[SupervisedTemplate]:
        return LwF

    @classmethod
    def get_required(cls) -> set[str]:
        return (super(LwFBuildConfig, cls).get_required() or set()).union({'alpha', 'temperature'})

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(LwFBuildConfig, cls).get_optionals()

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: UserWorkspaceResourceContext) -> TBoolStr:
        return super(LwFBuildConfig, cls).validate_input(data, dtype, context)

    @classmethod
    def extra_create_params_process(cls, params: TDesc) -> TDesc:
        alpha = params['alpha']
        alpha_for_all = True if isinstance(alpha, float) else False
        alpha = [alpha] if alpha_for_all else alpha
        params['alpha'] = alpha
        params['alpha_for_all'] = alpha_for_all
        return params

    def extra_build_params_process(self) -> TDesc:
        alpha = self.alpha[0] if self.alpha_for_all else self.alpha
        return {'alpha': alpha, 'temperature': self.temperature}


# Elastic Weights Consolidation
@MongoBuildConfig.register_build_config('EWC')
class EWCBuildConfig(MongoBaseStrategyBuildConfig):

    # Fields
    ewc_lambda = db.FloatField(required=True)
    mode = db.StringField(default="separate")
    decay_factor = db.FloatField(default=None)
    keep_importance_data = db.BooleanField(default=False)

    def to_dict(self, links=True) -> TDesc:
        data = super().to_dict(links=links)
        data.update({
            'ewc_lambda': self.ewc_lambda,
            'mode': self.mode,
            'decay_factor': self.decay_factor,
            'keep_importance_data': self.keep_importance_data,
        })
        return data

    @classmethod
    def schema_dict(cls) -> dict:
        data = super(EWCBuildConfig, cls).schema_dict()
        data.update({
            'ewc_lambda': float,
            sch.Optional('mode'): str,
            sch.Optional('decay_factor'): float,
            sch.Optional('keep_importance_data', default=False): bool,
        })
        return data

    @staticmethod
    def get_avalanche_strategy() -> t.Type[SupervisedTemplate]:
        return EWC

    @classmethod
    def get_required(cls) -> set[str]:
        return super(EWCBuildConfig, cls).get_required().union({'ewc_lambda'})

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(EWCBuildConfig, cls).get_optionals().union({'mode', 'decay_factor', 'keep_importance_data'})

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: UserWorkspaceResourceContext) -> TBoolStr:
        return super(EWCBuildConfig, cls).validate_input(data, dtype, context)

    @classmethod
    def extra_create_params_process(cls, params: TDesc) -> TDesc:
        mode = params.get('mode', 'separate')
        decay_factor = params.get('decay_factor')
        keep_importance_data = params.get('keep_importance_data', False)
        params['mode'] = mode
        params['keep_importance_data'] = keep_importance_data
        params['decay_factor'] = decay_factor
        return params

    def extra_build_params_process(self) -> TDesc:
        return {
            'ewc_lambda': self.ewc_lambda,
            'mode': self.mode,
            'decay_factor': self.decay_factor,
            'keep_importance_data': self.keep_importance_data,
        }


# (Classic) Replay
@MongoBuildConfig.register_build_config('Replay')
class ReplayBuildConfig(MongoBaseStrategyBuildConfig):

    # Fields
    memory = db.IntField(default=200)

    def to_dict(self, links=True) -> TDesc:
        data = super().to_dict(links=links)
        data.update({'memory': self.memory})
        return data

    @classmethod
    def schema_dict(cls) -> dict:
        data = super(ReplayBuildConfig, cls).schema_dict()
        data.update({
            sch.Optional('memory'): int,
        })
        return data

    @staticmethod
    def get_avalanche_strategy() -> t.Type[SupervisedTemplate]:
        return Replay

    @classmethod
    def get_required(cls) -> set[str]:
        return super(ReplayBuildConfig, cls).get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(ReplayBuildConfig, cls).get_optionals().union({'memory'})

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: UserWorkspaceResourceContext) -> TBoolStr:
        return super(ReplayBuildConfig, cls).validate_input(data, dtype, context)

    @classmethod
    def extra_create_params_process(cls, params: TDesc) -> TDesc:
        return params

    def extra_build_params_process(self) -> TDesc:
        return {'mem_size': self.memory}


@MongoBuildConfig.register_build_config('CWRStar')
class CWRStarBuildConfig(MongoBaseStrategyBuildConfig):

    # Fields
    layer_name = db.StringField(default=None)

    def to_dict(self, links=True) -> TDesc:
        data = super().to_dict(links=links)
        data.update({'layer_name': self.layer_name})
        return data

    @classmethod
    def schema_dict(cls) -> dict:
        data = super(CWRStarBuildConfig, cls).schema_dict()
        data.update({
            sch.Optional('layer_name'): str,
        })
        return data

    @classmethod
    def get_required(cls) -> set[str]:
        return super(CWRStarBuildConfig, cls).get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(CWRStarBuildConfig, cls).get_optionals().union({'layer_name'})

    @staticmethod
    def get_avalanche_strategy() -> t.Type[SupervisedTemplate]:
        return CWRStar

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: UserWorkspaceResourceContext) -> TBoolStr:
        return super(CWRStarBuildConfig, cls).validate_input(data, dtype, context)

    @classmethod
    def extra_create_params_process(cls, params: TDesc) -> TDesc:
        return params

    def extra_build_params_process(self) -> TDesc:
        return {'cwr_layer_name': self.layer_name}


@MongoBuildConfig.register_build_config('GDumb')
class GDumbBuildConfig(MongoBaseStrategyBuildConfig):

    # Fields
    memory = db.IntField(default=200)

    def to_dict(self, links=True) -> TDesc:
        data = super().to_dict(links=links)
        data.update({'memory': self.memory})
        return data

    @classmethod
    def schema_dict(cls) -> dict:
        data = super(GDumbBuildConfig, cls).schema_dict()
        data.update({
            sch.Optional('memory'): int,
        })
        return data

    @staticmethod
    def get_avalanche_strategy() -> t.Type[SupervisedTemplate]:
        return GDumb

    @classmethod
    def get_required(cls) -> set[str]:
        return super(GDumbBuildConfig, cls).get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(GDumbBuildConfig, cls).get_optionals().union({'memory'})

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: UserWorkspaceResourceContext) -> TBoolStr:
        return super(GDumbBuildConfig, cls).validate_input(data, dtype, context)

    @classmethod
    def extra_create_params_process(cls, params: TDesc) -> TDesc:
        return params

    def extra_build_params_process(self) -> TDesc:
        return {'mem_size': self.memory}


@MongoBuildConfig.register_build_config('AGEM')
class AGEMBuildConfig(MongoBaseStrategyBuildConfig):

    # Fields
    patterns_per_size = db.IntField(required=True)
    sample_size = db.IntField(default=64)

    def to_dict(self, links=True) -> TDesc:
        data = super().to_dict(links=links)
        data.update({
            'patterns_per_size': self.patterns_per_size,
            'sample_size': self.sample_size,
        })
        return data

    @classmethod
    def schema_dict(cls) -> dict:
        data = super(AGEMBuildConfig, cls).schema_dict()
        data.update({
            'patterns_per_size': int,
            sch.Optional('sample_size'): int,
        })
        return data

    @staticmethod
    def get_avalanche_strategy() -> t.Type[SupervisedTemplate]:
        return AGEM

    @classmethod
    def get_required(cls) -> set[str]:
        return super(AGEMBuildConfig, cls).get_required().union({'patterns_per_size'})

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(AGEMBuildConfig, cls).get_optionals().union({'sample_size'})

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: UserWorkspaceResourceContext) -> TBoolStr:
        return super(AGEMBuildConfig, cls).validate_input(data, dtype, context)

    @classmethod
    def extra_create_params_process(cls, params: TDesc) -> TDesc:
        return params

    def extra_build_params_process(self) -> TDesc:
        return {
            'patterns_per_size': self.patterns_per_size,
            'sample_size': self.sample_size,
        }


__all__ = [
    # Basic strategies
    'NaiveBuildConfig',
    'CumulativeBuildConfig',
    'JointTrainingBuildConfig',

    'SynapticIntelligenceBuildConfig',
    'LwFBuildConfig',
    'EWCBuildConfig',

    'ReplayBuildConfig',
    'GDumbBuildConfig',

    'CWRStarBuildConfig',
    'AGEMBuildConfig',
]