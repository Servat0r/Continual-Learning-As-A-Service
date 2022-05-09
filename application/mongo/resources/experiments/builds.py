from __future__ import annotations

from application.database import db
from application.utils import TBoolStr, t, TDesc
from application.models import User, Workspace

from application.resources.contexts import ResourceContext, UserWorkspaceResourceContext
from application.resources.base import DataType
from application.resources.datatypes import BaseCLExperiment

from application.mongo.resources.mongo_base_configs import *
from application.mongo.models import MongoUser, MongoWorkspace
from application.mongo.resources.strategies import MongoStrategy
from application.mongo.resources.benchmarks import MongoBenchmark


@MongoBuildConfig.register_build_config('ExperimentBuild')
class StandardExperimentBuildConfig(MongoBuildConfig):

    # Fields
    strategy = db.ReferenceField(MongoStrategy.config_type())
    benchmark = db.ReferenceField(MongoBenchmark.config_type())
    status = db.StringField(default=BaseCLExperiment.CREATED)

    @classmethod
    def get_required(cls) -> set[str]:
        return {'strategy', 'benchmark'}

    @classmethod
    def get_optionals(cls) -> set[str]:
        return set()

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

        owner = t.cast(MongoUser, User.canonicalize(context.get_username()))
        workspace = t.cast(MongoWorkspace, Workspace.canonicalize(context))

        strategy = MongoStrategy.config_type().get_one(owner, workspace, strategy_name)
        benchmark = MongoBenchmark.config_type().get_one(owner, workspace, benchmark_name)

        if strategy is None or benchmark is None:
            return False, "One or more referred resource(s) do(es) not exist."
        else:
            params['strategy'] = strategy
            params['benchmark'] = benchmark
            context.push(iname, values)
            return True, None

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super().create(data, tp, context)

    def build(self, context: ResourceContext):
        strategy = self.strategy.build(context)
        benchmark = self.benchmark.build(context)
        # noinspection PyArgumentList
        return self.target_type()(strategy, benchmark, self.status)