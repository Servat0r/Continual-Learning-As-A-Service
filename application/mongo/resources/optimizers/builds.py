from __future__ import annotations
from torch.optim import SGD, Adam

from application.utils import t, TDesc, TBoolStr
from application.database import db
from application.models import User, Workspace

from application.resources.contexts import ResourceContext, UserWorkspaceResourceContext
from application.resources.base import DataType

from application.mongo.resources.mongo_base_configs import *
from application.mongo.base import MongoBaseUser
from application.mongo.resources.models import MongoModelConfig


# SGD
@MongoBuildConfig.register_build_config('SGD')
class SGDBuildConfig(MongoBuildConfig):

    learning_rate = db.FloatField(required=True)
    momentum = db.FloatField(default=0.0)
    dampening = db.FloatField(default=0.0)
    weight_decay = db.FloatField(default=0.0)
    nesterov = db.BooleanField(default=False)
    model = db.ReferenceField(MongoModelConfig, required=True)  # for parameters

    @classmethod
    def get_required(cls) -> set[str]:
        return {'model', 'learning_rate'}

    @classmethod
    def get_optionals(cls) -> set[str]:
        return {
            'momentum',
            'dampening',
            'weight_decay',
            'nesterov',
        }

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type("CLOptimizer")

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: UserWorkspaceResourceContext) -> TBoolStr:
        result, msg = super().validate_input(data, dtype, context)
        if not result:
            return result, msg

        iname, values = context.head()
        params: TDesc = values['params']

        learning_rate = params.get('learning_rate') or 0.0
        momentum = params.get('momentum') or 0.0
        dampening = params.get('dampening') or 0.0
        weight_decay = params.get('weight_decay') or 0.0

        float_check = all(isinstance(param, float) for param in {
            learning_rate, momentum, dampening, weight_decay,
        })

        if not float_check:
            return False, "One or more parameters are not in the correct type."

        model_name = params['model']
        owner = t.cast(MongoBaseUser, User.canonicalize(context.get_username()))
        workspace = Workspace.canonicalize(context)

        model = MongoModelConfig.get_one(owner, workspace, model_name)
        if not model:
            return False, "One or more referred resource does not exist."
        else:
            params['model'] = model
            context.push(iname, values)
            return True, None

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super().create(data, tp, context, save)

    def build(self, context: ResourceContext):
        model = self.model.build(context)
        params = model.get_value().parameters()
        optimizer = SGD(params, self.learning_rate, self.momentum,
                        self.dampening, self.weight_decay, self.nesterov)

        # noinspection PyArgumentList
        return self.target_type()(optimizer)


# Adam
@MongoBuildConfig.register_build_config('Adam')
class AdamBuildConfig(MongoBuildConfig):

    learning_rate = db.FloatField(required=True)
    eps = db.FloatField(default=1e-8)
    weight_decay = db.FloatField(default=0.0)
    model = db.ReferenceField(MongoModelConfig, required=True)

    @classmethod
    def get_required(cls) -> set[str]:
        return {'model', 'learning_rate'}

    @classmethod
    def get_optionals(cls) -> set[str]:
        return {
            'eps',
            'weight_decay',
        }

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type('CLOptimizer')

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: UserWorkspaceResourceContext) -> TBoolStr:

        result, msg = super().validate_input(data, dtype, context)
        if not result:
            return result, msg

        iname, values = context.head()
        params: TDesc = values['params']

        learning_rate = params.get('learning_rate', 0.0)
        eps = params.get('eps', 1e-8)
        weight_decay = params.get('weight_decay', 0.0)

        float_check = all(isinstance(param, float) for param in {
            learning_rate, eps, weight_decay,
        })

        if not float_check:
            return False, "One or more parameters are not in the correct type."

        model_name = params['model']
        owner = t.cast(MongoBaseUser, User.canonicalize(context.get_username()))
        workspace = Workspace.canonicalize(context)

        model = MongoModelConfig.get_one(owner, workspace, model_name)
        if not model:
            return False, "One or more referred resource does not exist."
        else:
            params['model'] = model
            params['learning_rate'] = learning_rate
            params['eps'] = eps
            params['weight_decay'] = weight_decay
            context.push(iname, values)
            return True, None

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super().create(data, tp, context, save)

    def build(self, context: ResourceContext):
        model = self.model.build(context)
        params = model.get_value().parameters()
        optimizer = Adam(params, lr=self.learning_rate, eps=self.eps, weight_decay=self.weight_decay)
        # noinspection PyArgumentList
        return self.target_type()(optimizer)


__all__ = [
    'SGDBuildConfig',
    'AdamBuildConfig',
]