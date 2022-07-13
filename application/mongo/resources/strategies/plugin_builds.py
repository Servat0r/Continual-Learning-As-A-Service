from __future__ import annotations

import schema as sch

from avalanche.core import SupervisedPlugin
from avalanche.training.plugins import ReplayPlugin, GDumbPlugin, SynapticIntelligencePlugin, \
    LwFPlugin, EWCPlugin, AGEMPlugin

from application.utils import TBoolStr, TDesc
from application.database import db
from application.resources.contexts import UserWorkspaceResourceContext

from .base_builds import *


@StrategyPluginConfig.register_plugin_config('SynapticIntelligence')
class SynapticIntelligencePluginConfig(StrategyPluginConfig):

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

    @classmethod
    def get_required(cls) -> set[str]:
        return (super().get_required() or set()).union({'si_lambda'})

    @classmethod
    def get_optionals(cls) -> set[str]:
        return (super().get_optionals() or set()).union({'eps'})

    @classmethod
    def validate_input(cls, data: TDesc, context: UserWorkspaceResourceContext) -> TBoolStr:
        return super().validate_input(data, context)

    @classmethod
    def extra_create_params_process(cls, params: TDesc) -> TDesc:
        si_lambda = params['si_lambda']
        si_lambda_for_all = True if isinstance(si_lambda, float) else False
        si_lambda = [si_lambda] if si_lambda_for_all else si_lambda
        params['si_lambda'] = si_lambda
        params['si_lambda_for_all'] = si_lambda_for_all
        return params

    def get_plugin(self) -> SupervisedPlugin:
        si_lambda = self.si_lambda[0] if self.si_lambda_for_all else self.si_lambda
        return SynapticIntelligencePlugin(si_lambda, self.eps)


@StrategyPluginConfig.register_plugin_config('Replay')
class ReplayPluginConfig(StrategyPluginConfig):

    # Fields
    memory = db.IntField(default=200)

    def to_dict(self, links=True) -> TDesc:
        data = super().to_dict(links=links)
        data.update({'memory': self.memory})
        return data

    @classmethod
    def schema_dict(cls) -> dict:
        data = super(ReplayPluginConfig, cls).schema_dict()
        data.update({
            sch.Optional('memory'): int,
        })
        return data

    @classmethod
    def get_required(cls) -> set[str]:
        return super(ReplayPluginConfig, cls).get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(ReplayPluginConfig, cls).get_optionals().union({'memory'})

    @classmethod
    def validate_input(cls, data: TDesc, context: UserWorkspaceResourceContext) -> TBoolStr:
        return super(ReplayPluginConfig, cls).validate_input(data, context)

    @classmethod
    def extra_create_params_process(cls, params: TDesc) -> TDesc:
        return params

    def get_plugin(self) -> SupervisedPlugin:
        return ReplayPlugin(mem_size=self.memory)


@StrategyPluginConfig.register_plugin_config('LwF')
class LwFPluginConfig(StrategyPluginConfig):

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
        data = super(LwFPluginConfig, cls).schema_dict()
        data.update({
            'alpha': sch.Or(float, [float]),
            'temperature': float,
        })
        return data

    @classmethod
    def validate_input(cls, data: TDesc, context: UserWorkspaceResourceContext) -> TBoolStr:
        return super(LwFPluginConfig, cls).validate_input(data, context)

    @classmethod
    def extra_create_params_process(cls, params: TDesc) -> TDesc:
        alpha = params['alpha']
        alpha_for_all = True if isinstance(alpha, float) else False
        alpha = [alpha] if alpha_for_all else alpha
        params['alpha'] = alpha
        params['alpha_for_all'] = alpha_for_all
        return params

    def get_plugin(self) -> SupervisedPlugin:
        alpha = self.alpha[0] if self.alpha_for_all else self.alpha
        return LwFPlugin(alpha=alpha, temperature=self.temperature)


@StrategyPluginConfig.register_plugin_config('EWC')
class EWCPluginConfig(StrategyPluginConfig):

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
        data = super(EWCPluginConfig, cls).schema_dict()
        data.update({
            'ewc_lambda': float,
            sch.Optional('mode'): str,
            sch.Optional('decay_factor'): float,
            sch.Optional('keep_importance_data', default=False): bool,
        })
        return data

    @classmethod
    def validate_input(cls, data: TDesc, context: UserWorkspaceResourceContext) -> TBoolStr:
        return super(EWCPluginConfig, cls).validate_input(data, context)

    @classmethod
    def extra_create_params_process(cls, params: TDesc) -> TDesc:
        mode = params.get('mode', 'separate')
        decay_factor = params.get('decay_factor')
        keep_importance_data = params.get('keep_importance_data', False)
        params['mode'] = mode
        params['keep_importance_data'] = keep_importance_data
        params['decay_factor'] = decay_factor
        return params

    def get_plugin(self) -> SupervisedPlugin:
        return EWCPlugin(
            self.ewc_lambda, self.mode,
            self.decay_factor, self.keep_importance_data,
        )


@StrategyPluginConfig.register_plugin_config('GDumb')
class GDumbPluginConfig(StrategyPluginConfig):

    # Fields
    memory = db.IntField(default=200)

    def to_dict(self, links=True) -> TDesc:
        data = super().to_dict(links=links)
        data.update({'memory': self.memory})
        return data

    @classmethod
    def schema_dict(cls) -> dict:
        data = super(GDumbPluginConfig, cls).schema_dict()
        data.update({
            sch.Optional('memory'): int,
        })
        return data

    @classmethod
    def get_required(cls) -> set[str]:
        return super(GDumbPluginConfig, cls).get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(GDumbPluginConfig, cls).get_optionals().union({'memory'})

    @classmethod
    def validate_input(cls, data: TDesc, context: UserWorkspaceResourceContext) -> TBoolStr:
        return super(GDumbPluginConfig, cls).validate_input(data, context)

    @classmethod
    def extra_create_params_process(cls, params: TDesc) -> TDesc:
        return params

    def get_plugin(self) -> SupervisedPlugin:
        return GDumbPlugin(mem_size=self.memory)


@StrategyPluginConfig.register_plugin_config('AGEM')
class AGEMPluginConfig(StrategyPluginConfig):

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
        data = super(AGEMPluginConfig, cls).schema_dict()
        data.update({
            'patterns_per_size': int,
            sch.Optional('sample_size'): int,
        })
        return data

    @classmethod
    def get_required(cls) -> set[str]:
        return super(AGEMPluginConfig, cls).get_required().union({'patterns_per_size'})

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(AGEMPluginConfig, cls).get_optionals().union({'sample_size'})

    @classmethod
    def validate_input(cls, data: TDesc, context: UserWorkspaceResourceContext) -> TBoolStr:
        return super(AGEMPluginConfig, cls).validate_input(data, context)

    @classmethod
    def extra_create_params_process(cls, params: TDesc) -> TDesc:
        return params

    def get_plugin(self) -> SupervisedPlugin:
        return AGEMPlugin(
            patterns_per_experience=self.patterns_per_size,
            sample_size=self.sample_size,
        )


__all__ = [
    'SynapticIntelligencePluginConfig',
    'ReplayPluginConfig',
    'LwFPluginConfig',
    'EWCPluginConfig',
    'GDumbPluginConfig',
    'AGEMPluginConfig',
]