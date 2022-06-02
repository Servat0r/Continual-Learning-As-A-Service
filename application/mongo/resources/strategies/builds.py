from __future__ import annotations
from avalanche.training.templates import SupervisedTemplate
from avalanche.training.supervised import Naive, Cumulative, \
    SynapticIntelligence, LwF, Replay, CWRStar, GDumb, AGEM, JointTraining

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


@MongoBuildConfig.register_build_config('JointTraining')
class JointTrainingBuildConfig(MongoBaseStrategyBuildConfig):

    @staticmethod
    def get_avalanche_strategy() -> t.Type[SupervisedTemplate]:
        return JointTraining

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
    si_lambda_for_all = db.BooleanField(default=False)
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
    def create(cls, data: TDesc, tp: t.Type[DataType], context: UserWorkspaceResourceContext, save: bool = True):
        ok, bc_name, params, extras = cls._filter_data(data)
        model_name = params['model']
        optim_name = params['optimizer']
        criterion_name = params['criterion']
        metricset_name = params['metricset']
        si_lambda = params['si_lambda']
        si_lambda_for_all = True if isinstance(si_lambda, float) else False
        si_lambda = [si_lambda] if si_lambda_for_all else si_lambda

        owner = t.cast(MongoBaseUser, User.canonicalize(context.get_username()))
        workspace = Workspace.canonicalize(context)

        model = MongoModel.config_type().get_one(owner, workspace, model_name)
        optim = MongoCLOptimizer.config_type().get_one(owner, workspace, optim_name)
        criterion = MongoCLCriterion.config_type().get_one(owner, workspace, criterion_name)
        metricset = MongoStandardMetricSet.config_type().get_one(owner, workspace, metricset_name)

        params['model'] = model
        params['optimizer'] = optim
        params['criterion'] = criterion
        params['metricset'] = metricset
        params['si_lambda'] = si_lambda
        params['si_lambda_for_all'] = si_lambda_for_all

        # noinspection PyArgumentList
        return cls(**params)

    def build(self, context: UserWorkspaceResourceContext, locked=False, parents_locked=False):
        model = self.model.build(context, locked=locked, parents_locked=parents_locked)
        optim = self.optimizer.build(context, locked=locked, parents_locked=parents_locked)
        criterion = self.criterion.build(context, locked=locked, parents_locked=parents_locked)

        log_folder = self.get_logging_path(context)
        metricset = self.metricset.build(context)

        si_lambda = self.si_lambda[0] if self.si_lambda_for_all else self.si_lambda

        strategy = SynapticIntelligence(
            model.get_value(), optim.get_value(), criterion.get_value(),
            si_lambda=si_lambda, eps=self.eps, device=get_device(),
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
    alpha_for_all = db.BooleanField(default=False)
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
    def create(cls, data: TDesc, tp: t.Type[DataType], context: UserWorkspaceResourceContext, save: bool = True):
        ok, bc_name, params, extras = cls._filter_data(data)
        model_name = params['model']
        optim_name = params['optimizer']
        criterion_name = params['criterion']
        metricset_name = params['metricset']
        alpha = params['alpha']
        alpha_for_all = True if isinstance(alpha, float) else False
        alpha = [alpha] if alpha_for_all else alpha

        owner = t.cast(MongoBaseUser, User.canonicalize(context.get_username()))
        workspace = Workspace.canonicalize(context)

        model = MongoModel.config_type().get_one(owner, workspace, model_name)
        optim = MongoCLOptimizer.config_type().get_one(owner, workspace, optim_name)
        criterion = MongoCLCriterion.config_type().get_one(owner, workspace, criterion_name)
        metricset = MongoStandardMetricSet.config_type().get_one(owner, workspace, metricset_name)

        params['model'] = model
        params['optimizer'] = optim
        params['criterion'] = criterion
        params['metricset'] = metricset
        params['alpha'] = alpha
        params['alpha_for_all'] = alpha_for_all

        # noinspection PyArgumentList
        return cls(**params)

    def build(self, context: UserWorkspaceResourceContext, locked=False, parents_locked=False):
        model = self.model.build(context, locked=locked, parents_locked=parents_locked)
        optim = self.optimizer.build(context, locked=locked, parents_locked=parents_locked)
        criterion = self.criterion.build(context, locked=locked, parents_locked=parents_locked)

        log_folder = self.get_logging_path(context)
        metricset = self.metricset.build(context)

        alpha = self.alpha[0] if self.alpha_for_all else self.alpha

        strategy = LwF(
            model.get_value(), optim.get_value(), criterion.get_value(),
            alpha=alpha, temperature=self.temperature, device=get_device(),
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
    # Basic strategies
    'NaiveBuildConfig',
    'CumulativeBuildConfig',
    'JointTrainingBuildConfig',

    'SynapticIntelligenceBuildConfig',
    'LwFBuildConfig',

    'ReplayBuildConfig',
    'GDumbBuildConfig',

    'CWRStarBuildConfig',
    'AGEMBuildConfig',
]