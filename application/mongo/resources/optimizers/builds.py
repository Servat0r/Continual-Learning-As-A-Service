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

    def to_dict(self, links=True) -> TDesc:
        data = super().to_dict(links=links)
        data.update({
            'learning_rate': self.learning_rate,
            'momentum': self.momentum,
            'dampening': self.dampening,
            'weight_decay': self.weight_decay,
            'nesterov': self.nesterov,
            'model': self.model.to_dict(links=False) if links else self.model.get_name(),
        })
        return data

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

        iname, values = context.pop()
        params: TDesc = values['params']

        learning_rate = params.get('learning_rate', 0.0)
        momentum = params.get('momentum', 0.0)
        dampening = params.get('dampening', 0.0)
        weight_decay = params.get('weight_decay', 0.0)
        nesterov = params.get('nesterov', False)

        float_check = all(isinstance(param, float) for param in {
            learning_rate, momentum, dampening, weight_decay, nesterov,
        })

        if not float_check:
            return False, "One or more parameters are not in the correct type."

        model_name = params['model']
        owner = t.cast(MongoBaseUser, User.canonicalize(context.get_username()))
        workspace = Workspace.canonicalize(context)

        model = MongoModelConfig.get_one(owner, workspace, model_name)
        if not model:
            return False, "One or more referred resource does not exist."
        return True, None

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: UserWorkspaceResourceContext, save: bool = True):
        ok, bc_name, params, extras = cls._filter_data(data)
        learning_rate = params.get('learning_rate', 0.0)
        momentum = params.get('momentum', 0.0)
        dampening = params.get('dampening', 0.0)
        weight_decay = params.get('weight_decay', 0.0)
        nesterov = params.get('nesterov', False)

        model_name = params['model']
        owner = t.cast(MongoBaseUser, User.canonicalize(context.get_username()))
        workspace = Workspace.canonicalize(context)

        model = MongoModelConfig.get_one(owner, workspace, model_name)
        # noinspection PyArgumentList
        return cls(
            learning_rate=learning_rate,
            momentum=momentum,
            dampening=dampening,
            weight_decay=weight_decay,
            nesterov=nesterov,
            model=model,
        )

    def build(self, context: ResourceContext, locked=False, parents_locked=False):
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

    def to_dict(self, links=True) -> TDesc:
        data = super().to_dict(links=links)
        data.update({
            'learning_rate': self.learning_rate,
            'eps': self.eps,
            'weight_decay': self.weight_decay,
            'model': self.model.to_dict(links=False) if links else self.model.get_name(),
        })
        return data

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

        iname, values = context.pop()
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
        return True, None

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: UserWorkspaceResourceContext, save: bool = True):
        ok, bc_name, params, extras = cls._filter_data(data)

        learning_rate = params.get('learning_rate', 0.0)
        eps = params.get('eps', 1e-8)
        weight_decay = params.get('weight_decay', 0.0)

        model_name = params['model']
        owner = t.cast(MongoBaseUser, User.canonicalize(context.get_username()))
        workspace = Workspace.canonicalize(context)
        model = MongoModelConfig.get_one(owner, workspace, model_name)

        # noinspection PyArgumentList
        return cls(
            learning_rate=learning_rate,
            eps=eps,
            weight_decay=weight_decay,
            model=model,
        )

    def build(self, context: ResourceContext, locked=False, parents_locked=False):
        model = self.model.build(context, locked=locked, parents_locked=parents_locked)
        params = model.get_value().parameters()
        optimizer = Adam(params, lr=self.learning_rate, eps=self.eps, weight_decay=self.weight_decay)
        # noinspection PyArgumentList
        return self.target_type()(optimizer)


__all__ = [
    'SGDBuildConfig',
    'AdamBuildConfig',
]