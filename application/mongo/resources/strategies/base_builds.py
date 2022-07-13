from __future__ import annotations

import schema as sch

from avalanche.core import SupervisedPlugin
from avalanche.training.templates import SupervisedTemplate
from avalanche.training.plugins import EvaluationPlugin

from application.database import db
from application.utils import abstractmethod, get_device, t, TDesc, TBoolStr
from application.data_managing import BaseDataManager
from application.models import User, Workspace

from application.resources.contexts import ResourceContext, UserWorkspaceResourceContext
from application.resources.base import DataType
from application.resources.datatypes import StandardMetricSet

from application.mongo.base import MongoBaseUser
from application.mongo.loggers import ExtendedCSVLogger

from application.mongo.resources.mongo_base_configs import MongoBuildConfig, MongoEmbeddedBuildConfig
from application.mongo.resources.metricsets import *
from application.mongo.resources.criterions import *
from application.mongo.resources.optimizers import *
from application.mongo.resources.models import *


# Base class for StrategyPlugins
class StrategyPluginConfig(MongoEmbeddedBuildConfig):

    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    __CONFIGS__: TDesc = {}

    def to_dict(self, links=True) -> TDesc:
        return super().to_dict(links=links)

    @staticmethod
    def register_plugin_config(name: str = None):
        def registerer(cls):
            nonlocal name
            if name is None:
                name = cls.__name__
            StrategyPluginConfig.__CONFIGS__[name] = cls
            return cls

        return registerer

    @classmethod
    def get_by_name(cls, name: str | TDesc) -> StrategyPluginConfig | None:
        if isinstance(name, str):
            return cls.__CONFIGS__.get(name)
        elif isinstance(name, dict):
            cname = name.get('name')
            if cname is None:
                raise ValueError('Missing name')
            else:
                return cls.__CONFIGS__.get(cname)

    @classmethod
    def get_key(cls) -> str | None:
        for name, cl in cls.__CONFIGS__.items():
            if cls == cl:
                return name
        return None

    @classmethod
    def validate_input(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        return super(StrategyPluginConfig, cls).validate_input(data, context)

    @classmethod
    @abstractmethod
    def extra_create_params_process(cls, params: TDesc) -> TDesc:
        pass

    @classmethod
    def create(cls, data: TDesc, context: ResourceContext, save: bool = True):
        ok, bc_name, params, extras = cls._filter_data(data)    # Validation "skipped"
        actuals: TDesc = params
        if cls.has_extras():
            for item in extras.items():
                actuals[item[0]] = item[1]
        actuals = cls.extra_create_params_process(actuals)
        # noinspection PyArgumentList
        return cls(**actuals)

    @abstractmethod
    def get_plugin(self) -> SupervisedPlugin:
        pass

    @classmethod
    def get_required(cls) -> set[str]:
        return super(StrategyPluginConfig, cls).get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(StrategyPluginConfig, cls).get_optionals()


class MongoBaseStrategyBuildConfig(MongoBuildConfig):
    """
    Base class template for strategies build configs.
    """
    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    model = db.ReferenceField(MongoModelConfig, required=True)
    optimizer = db.ReferenceField(MongoCLOptimizerConfig, required=True)
    criterion = db.ReferenceField(MongoCLCriterionConfig, required=True)
    train_mb_size = db.IntField(default=1)
    train_epochs = db.IntField(default=1)
    eval_mb_size = db.IntField(default=None)
    eval_every = db.IntField(default=-1)
    metricset = db.ReferenceField(MongoStandardMetricSetConfig, required=True)
    plugins = db.ListField(db.EmbeddedDocumentField(StrategyPluginConfig), default=None)

    def to_dict(self, links=True) -> TDesc:
        data = super().to_dict(links=links)
        data.update({
            'model': self.model.to_dict(links=False) if links else self.model.get_name(),
            'optimizer': self.optimizer.to_dict(links=False) if links else self.optimizer.get_name(),
            'criterion': self.criterion.to_dict(links=False) if links else self.criterion.get_name(),
            'train_mb_size': self.train_mb_size,
            'train_epochs': self.train_epochs,
            'eval_mb_size': self.eval_mb_size,
            'eval_every': self.eval_every,
            'metricset': self.metricset.to_dict(links=False) if links else self.metricset.get_name(),
            'plugins': [plugin.to_dict(links=False) if links else plugin.get_name() for plugin in self.plugins],
        })
        return data

    @classmethod
    def schema_dict(cls) -> dict:
        data = super().schema_dict()
        data.update({
            'model': str,
            'optimizer': str,
            'criterion': str,
            'metricset': str,
            sch.Optional('train_mb_size'): int,
            sch.Optional('train_epochs'): int,
            sch.Optional('eval_mb_size'): int,
            sch.Optional('eval_every'): int,
            sch.Optional('plugins', default=[]): [{str: object}],
        })
        return data

    @staticmethod
    @abstractmethod
    def get_avalanche_strategy() -> t.Type[SupervisedTemplate]:
        pass

    @staticmethod
    def get_evaluator(log_folder: list[str], metricset: StandardMetricSet) -> EvaluationPlugin:
        return EvaluationPlugin(
            *metricset.get_value(),
            loggers=[
                ExtendedCSVLogger(log_folder=log_folder, metricset=metricset),
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
            'plugins',
        }

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type('Strategy')

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: UserWorkspaceResourceContext) -> TBoolStr:
        result, msg = super().validate_input(data, dtype, context)
        if not result:
            return result, msg
        plugins = data.get('plugins', None)
        if plugins is not None:
            if not isinstance(plugins, list):
                return False, "'plugins' parameter must be a list!"
            for plugin_data in plugins:
                if not isinstance(plugin_data, dict):
                    return False, "'plugins' items must be dictionaries!"
                plugin_config = StrategyPluginConfig.get_by_name(plugin_data)
                if plugin_config is None:
                    return False, f"Unknown plugin config name: '{plugin_data.get('name')}'"
                result, msg = plugin_config.validate_input(plugin_data, context)
                if not result:
                    return False, f"Failed to validate plugins data: '{msg}'"

        model_name = data['model']
        optim_name = data['optimizer']
        criterion_name = data['criterion']
        metricset_name = data['metricset']

        owner = t.cast(MongoBaseUser, User.canonicalize(context.get_username()))
        workspace = Workspace.canonicalize(context)

        model = MongoModel.config_type().get_one(owner, workspace, model_name)
        optim = MongoCLOptimizer.config_type().get_one(owner, workspace, optim_name)
        criterion = MongoCLCriterion.config_type().get_one(owner, workspace, criterion_name)
        metricset = MongoStandardMetricSet.config_type().get_one(owner, workspace, metricset_name)

        refs_check = all(res is not None for res in [model, optim, criterion, metricset])
        if not refs_check:
            return False, "One or more referred resource(s) do(es) not exist."
        return True, None

    @classmethod
    @abstractmethod
    def extra_create_params_process(cls, params: TDesc) -> TDesc:
        """
        Logic for converting strategy-specific extra parameters.
        :param params:
        :return: Updated dictionary.
        """
        pass

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

        plugins_data = params.get('plugins', None)
        plugins = []
        if plugins_data is not None:
            for plugin_data in plugins_data:
                plugin_config = StrategyPluginConfig.get_by_name(plugin_data)
                plugin = plugin_config.create(plugin_data, context, save=False)
                plugins.append(plugin)

        params['model'] = model
        params['optimizer'] = optim
        params['criterion'] = criterion
        params['metricset'] = metricset
        params['plugins'] = plugins

        params = cls.extra_create_params_process(params)

        # noinspection PyArgumentList
        return cls(**params)

    @abstractmethod
    def extra_build_params_process(self) -> TDesc:
        """
        Implements logic for strategy extra parameters.
        :return: A dictionary of the form {'param_name': param_value} that is passed
        to the corresponding Avalanche strategy.
        """
        pass

    def build(self, context: UserWorkspaceResourceContext, locked=False, parents_locked=False):
        model = self.model.build(context, locked=locked, parents_locked=parents_locked)
        optim = self.optimizer.build(context, locked=locked, parents_locked=parents_locked)
        criterion = self.criterion.build(context, locked=locked, parents_locked=parents_locked)

        log_folder = self.get_logging_path(context)
        metricset = self.metricset.build(context)

        plugins = None
        if self.plugins is not None and len(self.plugins) > 0:
            plugins = []
            for plugin_data in self.plugins:
                plugin = plugin_data.get_plugin()
                plugins.append(plugin)

        extra_params = self.extra_build_params_process()

        strategy = self.get_avalanche_strategy()(
            model.get_value(), optim.get_value(), criterion.get_value(),
            device=get_device(), **extra_params, plugins=plugins,
            train_mb_size=self.train_mb_size, train_epochs=self.train_epochs,
            eval_mb_size=self.eval_mb_size, eval_every=self.eval_every,
            evaluator=self.get_evaluator(log_folder, metricset),
        )
        # noinspection PyArgumentList
        return self.target_type()(strategy, model, optim, criterion, metricset)


__all__ = [
    'MongoBaseStrategyBuildConfig',
    'StrategyPluginConfig',
]