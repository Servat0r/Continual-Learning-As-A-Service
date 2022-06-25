from __future__ import annotations
from avalanche.core import SupervisedPlugin
from avalanche.training.plugins import ReplayPlugin, GDumbPlugin, SynapticIntelligencePlugin, \
    LwFPlugin, EWCPlugin, CWRStarPlugin, AGEMPlugin

from application.utils import TBoolStr, TDesc
from application.database import db
from application.resources.contexts import UserWorkspaceResourceContext

from application.mongo.resources.mongo_base_configs import *
from .base_builds import *


@StrategyPluginConfig.register_plugin_config('SynapticIntelligence')
class SynapticIntelligencePluginConfig(StrategyPluginConfig):

    # Fields
    si_lambda = db.ListField(db.FloatField(), required=True)
    si_lambda_for_all = db.BooleanField(default=False)
    eps = db.FloatField(default=0.0000001)

    @classmethod
    def get_required(cls) -> set[str]:
        return (super().get_required() or set()).union({'si_lambda'})

    @classmethod
    def get_optionals(cls) -> set[str]:
        return (super().get_optionals() or set()).union({'eps'})

    @classmethod
    def validate_input(cls, data: TDesc, context: UserWorkspaceResourceContext) -> TBoolStr:
        result, msg = super().validate_input(data, context)
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

    def get_plugin(self) -> SupervisedPlugin:
        si_lambda = self.si_lambda[0] if self.si_lambda_for_all else self.si_lambda
        return SynapticIntelligencePlugin(si_lambda, self.eps)


@StrategyPluginConfig.register_plugin_config('Replay')
class ReplayPluginConfig(StrategyPluginConfig):

    # Fields
    memory = db.IntField(default=200)

    @classmethod
    def get_required(cls) -> set[str]:
        return super(ReplayPluginConfig, cls).get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(ReplayPluginConfig, cls).get_optionals().union({'memory'})

    @classmethod
    def validate_input(cls, data: TDesc, context: UserWorkspaceResourceContext) -> TBoolStr:
        result, msg = super(ReplayPluginConfig, cls).validate_input(data, context)
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

    def get_plugin(self) -> SupervisedPlugin:
        return ReplayPlugin(mem_size=self.memory)


@StrategyPluginConfig.register_plugin_config('LwF')
class LwFPluginConfig(StrategyPluginConfig):

    # Fields
    alpha = db.ListField(db.FloatField(), required=True)
    alpha_for_all = db.BooleanField(default=False)
    temperature = db.FloatField(required=True)

    @classmethod
    def validate_input(cls, data: TDesc, context: UserWorkspaceResourceContext) -> TBoolStr:
        result, msg = super(LwFPluginConfig, cls).validate_input(data, context)
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

    @classmethod
    def validate_input(cls, data: TDesc, context: UserWorkspaceResourceContext) -> TBoolStr:
        result, msg = super(EWCPluginConfig, cls).validate_input(data, context)
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

    def get_plugin(self) -> SupervisedPlugin:
        return EWCPlugin(
            self.ewc_lambda, self.mode,
            self.decay_factor, self.keep_importance_data,
        )


__all__ = [
    'SynapticIntelligencePluginConfig',
    'ReplayPluginConfig',
    'LwFPluginConfig',
    'EWCPluginConfig',
]