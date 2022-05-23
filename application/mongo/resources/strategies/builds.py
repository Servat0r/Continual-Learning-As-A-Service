from __future__ import annotations
from avalanche.training.templates import SupervisedTemplate
from avalanche.training.supervised import Naive, Cumulative, \
    SynapticIntelligence, LwF, Replay, CWRStar, GDumb, AGEM

from application.utils import TBoolStr, t, TDesc, get_device
from application.database import db

from application.resources.contexts import UserWorkspaceResourceContext
from application.resources.base import DataType

from application.mongo.resources.mongo_base_configs import *
from .base_builds import *


# Naive strategy builder
@MongoBuildConfig.register_build_config('Naive')
class NaiveBuildConfig(MongoBaseStrategyBuildConfig):
    """
    Build config for Naive strategy.
    """
    @staticmethod
    def get_avalanche_strategy() -> t.Type[SupervisedTemplate]:
        return Naive

    @classmethod
    def get_required(cls) -> set[str]:
        return super().get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super().get_optionals()


# Cumulative strategy builder
@MongoBuildConfig.register_build_config('Cumulative')
class CumulativeBuildConfig(MongoBaseStrategyBuildConfig):

    @staticmethod
    def get_avalanche_strategy() -> t.Type[SupervisedTemplate]:
        return Cumulative

    @classmethod
    def get_required(cls) -> set[str]:
        return super().get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super().get_optionals()


# Synaptic Intelligence strategy builder
@MongoBuildConfig.register_build_config('SynapticIntelligence')
class SynapticIntelligenceBuildConfig(MongoBaseStrategyBuildConfig):

    # Fields
    si_lambda = db.ListField(db.FloatField(), required=True)
    eps = db.FloatField(default=0.0000001)

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
        if isinstance(si_lambda, list):
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

    def build(self, context: UserWorkspaceResourceContext, locked=False, parents_locked=False):
        model = self.model.build(context, locked=locked, parents_locked=parents_locked)
        optim = self.optimizer.build(context, locked=locked, parents_locked=parents_locked)
        criterion = self.criterion.build(context, locked=locked, parents_locked=parents_locked)

        log_folder = self.get_logging_path(context)
        metricset = self.metricset.build(context)

        strategy = SynapticIntelligence(
            model.get_value(), optim.get_value(), criterion.get_value(),
            si_lambda=self.si_lambda, eps=self.eps, device=get_device(),
            train_mb_size=self.train_mb_size, train_epochs=self.train_epochs,
            eval_mb_size=self.eval_mb_size, eval_every=self.eval_every,
            evaluator=self.get_evaluator(log_folder, metricset),
        )
        # noinspection PyArgumentList
        return self.target_type()(strategy, model, optim, criterion, metricset)


@MongoBuildConfig.register_build_config('LwF')
class LwFBuildConfig(MongoBaseStrategyBuildConfig):

    # Fields
    alpha = db.ListField(db.FloatField(), required=True)
    temperature = db.FloatField(required=True)

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

        alpha_checked = True
        if isinstance(alpha, list):
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

    def build(self, context: UserWorkspaceResourceContext, locked=False, parents_locked=False):
        model = self.model.build(context, locked=locked, parents_locked=parents_locked)
        optim = self.optimizer.build(context, locked=locked, parents_locked=parents_locked)
        criterion = self.criterion.build(context, locked=locked, parents_locked=parents_locked)

        log_folder = self.get_logging_path(context)
        metricset = self.metricset.build(context)

        strategy = LwF(
            model.get_value(), optim.get_value(), criterion.get_value(),
            alpha=self.alpha, temperature=self.temperature, device=get_device(),
            train_mb_size=self.train_mb_size, train_epochs=self.train_epochs,
            eval_mb_size=self.eval_mb_size, eval_every=self.eval_every,
            evaluator=self.get_evaluator(log_folder, metricset),
        )
        # noinspection PyArgumentList
        return self.target_type()(strategy, model, optim, criterion, metricset)


@MongoBuildConfig.register_build_config('Replay')
class ReplayBuildConfig(MongoBaseStrategyBuildConfig):

    # Fields
    memory = db.IntField(default=200)

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

    def build(self, context: UserWorkspaceResourceContext, locked=False, parents_locked=False):
        model = self.model.build(context, locked=locked, parents_locked=parents_locked)
        optim = self.optimizer.build(context, locked=locked, parents_locked=parents_locked)
        criterion = self.criterion.build(context, locked=locked, parents_locked=parents_locked)

        log_folder = self.get_logging_path(context)
        metricset = self.metricset.build(context)

        # noinspection PyArgumentList
        strategy = self.get_avalanche_strategy()(
            model.get_value(), optim.get_value(), criterion.get_value(),
            mem_size=self.memory, device=get_device(),
            train_mb_size=self.train_mb_size, train_epochs=self.train_epochs,
            eval_mb_size=self.eval_mb_size, eval_every=self.eval_every,
            evaluator=self.get_evaluator(log_folder, metricset),
        )
        # noinspection PyArgumentList
        return self.target_type()(strategy, model, optim, criterion, metricset)


@MongoBuildConfig.register_build_config('CWRStar')
class CWRStarBuildConfig(MongoBaseStrategyBuildConfig):

    # Fields
    layer_name = db.StringField(default=None)

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

    def build(self, context: UserWorkspaceResourceContext, locked=False, parents_locked=False):
        model = self.model.build(context, locked=locked, parents_locked=parents_locked)
        optim = self.optimizer.build(context, locked=locked, parents_locked=parents_locked)
        criterion = self.criterion.build(context, locked=locked, parents_locked=parents_locked)

        log_folder = self.get_logging_path(context)
        metricset = self.metricset.build(context)

        # noinspection PyArgumentList
        strategy = self.get_avalanche_strategy()(
            model.get_value(), optim.get_value(), criterion.get_value(),
            cwr_layer_name=self.layer_name, device=get_device(),
            train_mb_size=self.train_mb_size, train_epochs=self.train_epochs,
            eval_mb_size=self.eval_mb_size, eval_every=self.eval_every,
            evaluator=self.get_evaluator(log_folder, metricset),
        )
        # noinspection PyArgumentList
        return self.target_type()(strategy, model, optim, criterion, metricset)


@MongoBuildConfig.register_build_config('GDumb')
class GDumbBuildConfig(MongoBaseStrategyBuildConfig):

    # Fields
    memory = db.IntField(default=200)

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

    def build(self, context: UserWorkspaceResourceContext, locked=False, parents_locked=False):
        model = self.model.build(context, locked=locked, parents_locked=parents_locked)
        optim = self.optimizer.build(context, locked=locked, parents_locked=parents_locked)
        criterion = self.criterion.build(context, locked=locked, parents_locked=parents_locked)

        log_folder = self.get_logging_path(context)
        metricset = self.metricset.build(context)

        # noinspection PyArgumentList
        strategy = self.get_avalanche_strategy()(
            model.get_value(), optim.get_value(), criterion.get_value(),
            mem_size=self.memory, device=get_device(),
            train_mb_size=self.train_mb_size, train_epochs=self.train_epochs,
            eval_mb_size=self.eval_mb_size, eval_every=self.eval_every,
            evaluator=self.get_evaluator(log_folder, metricset),
        )
        # noinspection PyArgumentList
        return self.target_type()(strategy, model, optim, criterion, metricset)


@MongoBuildConfig.register_build_config('AGEM')
class AGEMBuildConfig(MongoBaseStrategyBuildConfig):

    # Fields
    patterns_per_size = db.IntField(required=True)
    sample_size = db.IntField(default=64)

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

    def build(self, context: UserWorkspaceResourceContext, locked=False, parents_locked=False):
        model = self.model.build(context, locked=locked, parents_locked=parents_locked)
        optim = self.optimizer.build(context, locked=locked, parents_locked=parents_locked)
        criterion = self.criterion.build(context, locked=locked, parents_locked=parents_locked)

        log_folder = self.get_logging_path(context)
        metricset = self.metricset.build(context)

        # noinspection PyArgumentList
        strategy = self.get_avalanche_strategy()(
            model.get_value(), optim.get_value(), criterion.get_value(),
            mem_size=self.memory, device=get_device(),
            train_mb_size=self.train_mb_size, train_epochs=self.train_epochs,
            eval_mb_size=self.eval_mb_size, eval_every=self.eval_every,
            evaluator=self.get_evaluator(log_folder, metricset),
        )
        # noinspection PyArgumentList
        return self.target_type()(strategy, model, optim, criterion, metricset)


__all__ = [
    'NaiveBuildConfig',
    'CumulativeBuildConfig',
    'SynapticIntelligenceBuildConfig',
    'LwFBuildConfig',
    'ReplayBuildConfig',
    'CWRStarBuildConfig',
    'GDumbBuildConfig',
    'AGEMBuildConfig',
]