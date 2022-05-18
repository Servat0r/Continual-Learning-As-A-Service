from __future__ import annotations
from avalanche.logging import InteractiveLogger
from avalanche.training.strategies import BaseStrategy
from avalanche.training.plugins import EvaluationPlugin

from application.utils import abstractmethod, os, get_device
from application.data_managing import BaseDataManager
from application.models import User, Workspace

from application.mongo.base import MongoBaseUser
from application.mongo.loggers import ExtendedCSVLogger

from application.mongo.resources.metricsets import *
from application.mongo.resources.criterions import *
from application.mongo.resources.optimizers import *
from application.mongo.resources.models import *


class MongoBaseStrategyBuildConfig(MongoBuildConfig):
    """
    Base class template for strategies build configs.
    """
    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    model = db.ReferenceField(MongoModelConfig, required=True)
    optimizer = db.ReferenceField(MongoCLOptimizerConfig, required=True)     # TODO Embed!
    criterion = db.ReferenceField(MongoCLCriterionConfig, required=True)     # TODO Embed!
    train_mb_size = db.IntField(default=1)
    train_epochs = db.IntField(default=1)
    eval_mb_size = db.IntField(default=None)
    eval_every = db.IntField(default=-1)
    metricset = db.ReferenceField(MongoStandardMetricSetConfig, required=True)

    @staticmethod
    @abstractmethod
    def get_avalanche_strategy() -> t.Type[BaseStrategy]:
        pass

    @staticmethod
    def get_evaluator(log_folder: list[str], metricset: StandardMetricSet) -> EvaluationPlugin:
        return EvaluationPlugin(
            *metricset.get_value(),
            loggers=[
                ExtendedCSVLogger(log_folder=log_folder, metricset=metricset),
                InteractiveLogger(),
            ]
        )

    @staticmethod
    def get_logging_path(context: UserWorkspaceResourceContext) -> list[str]:
        iname, values = context.head()
        if not isinstance(values, list):
            raise TypeError("Context parameter is not of the correct type!")
        context.pop()
        return [BaseDataManager.get().get_root()] + values

    @classmethod
    @abstractmethod
    def get_required(cls) -> set[str]:
        return {
            'model',
            'optimizer',
            'metricset',
        }

    @classmethod
    @abstractmethod
    def get_optionals(cls) -> set[str]:
        return {
            'criterion',
            'train_mb_size',
            'train_epochs',
            'eval_mb_size',
            'eval_every',
        }

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type('Strategy')

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: UserWorkspaceResourceContext) -> TBoolStr:
        result, msg = super().validate_input(data, dtype, context)
        if not result:
            return result, msg
        iname, values = context.pop()
        params: TDesc = values['params']

        train_mb_size = params.get('train_mb_size', 0)
        train_epochs = params.get('train_epochs', 0)
        eval_mb_size = params.get('eval_mb_size', 0)
        eval_every = params.get('eval_every', -1)
        int_check = all(isinstance(param, int) for param in {
            train_mb_size, train_epochs, eval_mb_size, eval_every,
        })
        if not int_check or eval_every < -1:
            return False, "One or more parameters are not in the correct type."

        model_name = params['model']
        optim_name = params['optimizer']
        criterion_name = params['criterion']
        metricset_name = params['metricset']

        owner = t.cast(MongoBaseUser, User.canonicalize(context.get_username()))
        workspace = Workspace.canonicalize(context)

        model = MongoModel.config_type().get_one(owner, workspace, model_name)
        optim = MongoCLOptimizer.config_type().get_one(owner, workspace, optim_name)
        criterion = MongoCLCriterion.config_type().get_one(owner, workspace, criterion_name)
        metricset = MongoStandardMetricSet.config_type().get_one(owner, workspace, metricset_name)

        refs_check = all(res is not None for res in [model, optim, criterion, metricset])
        if not refs_check:
            return False, "One or more referred resource(s) do(es) not exist."
        context.push(iname, values)
        return True, None

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: UserWorkspaceResourceContext, save: bool = True):
        ok, bc_name, params, extras = cls._filter_data(data)
        model_name = params['model']
        optim_name = params['optimizer']
        criterion_name = params['criterion']
        metricset_name = params['metricset']

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

        # noinspection PyArgumentList
        return cls(**params)

    def build(self, context: UserWorkspaceResourceContext, locked=False, parents_locked=False):
        model = self.model.build(context, locked=locked, parents_locked=parents_locked)
        optim = self.optimizer.build(context, locked=locked, parents_locked=parents_locked)
        criterion = self.criterion.build(context, locked=locked, parents_locked=parents_locked)

        log_folder = self.get_logging_path(context)
        metricset = self.metricset.build(context)

        strategy = self.get_avalanche_strategy()(
            model.get_value(), optim.get_value(),
            criterion.get_value(), device=get_device(),
            train_mb_size=self.train_mb_size, train_epochs=self.train_epochs,
            eval_mb_size=self.eval_mb_size, eval_every=self.eval_every,
            evaluator=self.get_evaluator(log_folder, metricset),
        )
        # noinspection PyArgumentList
        return self.target_type()(strategy, model, optim, criterion, metricset)


__all__ = ['MongoBaseStrategyBuildConfig']