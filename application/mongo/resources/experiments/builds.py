from __future__ import annotations

from application.database import db
from application.utils import TBoolStr, t, TDesc
from application.models import User, Workspace

from application.resources.contexts import ResourceContext, UserWorkspaceResourceContext
from application.resources.base import DataType
from application.resources.datatypes import BaseCLExperiment, BaseCLExperimentRunConfig

from application.mongo.resources.mongo_base_configs import *
from application.mongo.models import MongoUser, MongoWorkspace
from application.mongo.resources.strategies import MongoStrategyConfig
from application.mongo.resources.benchmarks import MongoBenchmarkConfig


@MongoBuildConfig.register_build_config('ExperimentBuild')
class StandardExperimentBuildConfig(MongoBuildConfig):

    # Fields
    strategy = db.ReferenceField(MongoStrategyConfig)
    benchmark = db.ReferenceField(MongoBenchmarkConfig)
    status = db.StringField(default=BaseCLExperiment.CREATED)
    run_config = db.StringField(default=BaseCLExperimentRunConfig.DFL_RUN_CONFIG_NAME)

    @classmethod
    def get_required(cls) -> set[str]:
        return {'strategy', 'benchmark'}

    @classmethod
    def get_optionals(cls) -> set[str]:
        return (super().get_optionals() or set()).union({'run_config'})

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type('BaseCLExperiment')

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: UserWorkspaceResourceContext) -> TBoolStr:
        result, msg = super().validate_input(data, dtype, context)
        if not result:
            return result, msg
        iname, values = context.pop()
        params: TDesc = values['params']

        strategy_name = params['strategy']
        benchmark_name = params['benchmark']
        run_config_name = params.get('run_config', BaseCLExperimentRunConfig.DFL_RUN_CONFIG_NAME)

        owner = t.cast(MongoUser, User.canonicalize(context.get_username()))
        workspace = t.cast(MongoWorkspace, Workspace.canonicalize(context))

        strategy = MongoStrategyConfig.get_one(owner, workspace, strategy_name)
        benchmark = MongoBenchmarkConfig.get_one(owner, workspace, benchmark_name)
        run_config = BaseCLExperimentRunConfig.get_by_name(run_config_name)

        if run_config is None:
            return False, f"The specified run configuration '{run_config_name}' does not exist."

        if strategy is None or benchmark is None:
            return False, "One or more referred resource(s) do(es) not exist."
        return True, None

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: UserWorkspaceResourceContext, save: bool = True):
        ok, bc_name, params, extras = cls._filter_data(data)

        strategy_name = params['strategy']
        benchmark_name = params['benchmark']
        run_config_name = params.get('run_config', BaseCLExperimentRunConfig.DFL_RUN_CONFIG_NAME)

        owner = t.cast(MongoUser, User.canonicalize(context.get_username()))
        workspace = t.cast(MongoWorkspace, Workspace.canonicalize(context))

        strategy = MongoStrategyConfig.get_one(owner, workspace, strategy_name)
        benchmark = MongoBenchmarkConfig.get_one(owner, workspace, benchmark_name)

        params['run_config'] = run_config_name
        params['strategy'] = strategy
        params['benchmark'] = benchmark
        # noinspection PyArgumentList
        return cls(**params)

    def build(self, context: ResourceContext, locked=False, parents_locked=False):

        strategy = self.strategy.build(context, locked=locked, parents_locked=parents_locked)
        benchmark = self.benchmark.build(context, locked=locked, parents_locked=parents_locked)
        # noinspection PyArgumentList
        return self.target_type()(strategy, benchmark, self.status, self.run_config)