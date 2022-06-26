from __future__ import annotations
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
        result, msg = super().validate_input(data, dtype, context)
        if not result:
            return result, msg

        iname, values = context.pop()
        params: TDesc = values['params']
        si_lambda = params['si_lambda']
        eps = params.get('eps', 0.0000001)

        si_checked = True
        if isinstance(si_lambda, float):
            si_checked = True
        elif isinstance(si_lambda, list):
            for si_l in si_lambda:
                if not isinstance(si_l, float):
                    si_checked = False
                    break
        else:
            si_checked = False
        if not si_checked:
            return False, "Parameter 'si_lambda' is not of the correct type."

        if not isinstance(eps, float):
            return False, "Parameter 'eps' is not of the correct type."

        return True, None


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
        result, msg = super(LwFBuildConfig, cls).validate_input(data, dtype, context)
        if not result:
            return result, msg

        iname, values = context.pop()
        params: TDesc = values['params']
        alpha = params['alpha']
        temperature = params['temperature']

        # alpha can be either a float or a list of floats
        alpha_checked = True
        if isinstance(alpha, float):
            alpha_checked = True
        elif isinstance(alpha, list):
            for a in alpha:
                if not isinstance(a, float):
                    alpha_checked = False
                    break
        else:
            alpha_checked = False
        if not alpha_checked:
            return False, "Parameter 'alpha' is not of the correct type."

        if not isinstance(temperature, float):
            return False, "Parameter 'temperature' is not of the correct type."
        return True, None

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
        result, msg = super(EWCBuildConfig, cls).validate_input(data, dtype, context)
        if not result:
            return result, msg

        iname, values = context.pop()
        params: TDesc = values['params']
        ewc_lambda = params['ewc_lambda']
        mode = params.get('mode', 'separate')
        decay_factor = params.get('decay_factor')
        keep_importance_data = params.get('keep_importance_data', False)

        if not isinstance(ewc_lambda, float):
            return False, "Parameter 'ewc_lambda' must be a float!"

        if not isinstance(mode, str):
            return False, "Parameter 'mode' must be a string!"

        if decay_factor is not None and not isinstance(decay_factor, float):
            return False, "Parameter 'decay_factor' must be a float!"

        if not isinstance(keep_importance_data, bool):
            return False, "Parameter 'keep_importance_data' must be a boolean!"

        return True, None

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
        result, msg = super(ReplayBuildConfig, cls).validate_input(data, dtype, context)
        if not result:
            return result, msg

        iname, values = context.pop()
        params: TDesc = values['params']
        memory = params.get('memory', 200)

        if not isinstance(memory, int):
            return False, "Parameter 'memory' is not of the correct type."
        return True, None

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
        result, msg = super(CWRStarBuildConfig, cls).validate_input(data, dtype, context)
        if not result:
            return result, msg

        iname, values = context.pop()
        params: TDesc = values['params']
        layer_name = params.get('layer_name', '')

        if not isinstance(layer_name, str):
            return False, "Parameter 'layer_name' is not of the correct type."
        return True, None

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
        result, msg = super(GDumbBuildConfig, cls).validate_input(data, dtype, context)
        if not result:
            return result, msg

        iname, values = context.pop()
        params: TDesc = values['params']
        memory = params.get('memory', 200)

        if not isinstance(memory, int):
            return False, "Parameter 'memory' is not of the correct type."
        return True, None

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
        result, msg = super(AGEMBuildConfig, cls).validate_input(data, dtype, context)
        if not result:
            return result, msg

        iname, values = context.pop()
        params: TDesc = values['params']
        patterns_per_size = params['patterns_per_size']
        sample_size = params.get('sample_size', 64)

        all_int = all(isinstance(val, int) for val in [patterns_per_size, sample_size])
        return (True, None) if all_int else (False, "Parameter 'memory' is not of the correct type.")

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