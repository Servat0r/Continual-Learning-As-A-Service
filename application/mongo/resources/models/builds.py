from __future__ import annotations
from avalanche.models.simple_mlp import SimpleMLP
from avalanche.models.simple_cnn import SimpleCNN
from avalanche.models.pnn import PNN

from application.utils import TBoolStr, t, TDesc
from application.database import db
# from application.avalanche_ext import *

from application.resources.contexts import ResourceContext
from application.resources.base import DataType

from application.mongo.resources.mongo_base_configs import *


# SimpleMLP builder
@MongoBuildConfig.register_build_config('SimpleMLP')
class SimpleMLPBuildConfig(MongoBuildConfig):
    """
    Build config for a SimpleMLP as defined in avalanche.models.simple_mlp#SimpleMLP
    """

    # fields, required, optionals
    num_classes = db.IntField(default=10)
    input_size = db.IntField(default=28*28)
    hidden_size = db.IntField(default=512)
    hidden_layers = db.IntField(default=1)
    drop_rate = db.IntField(default=0.5)

    @classmethod
    def get_required(cls) -> set[str]:
        return set()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return {
            'num_classes',
            'input_size',
            'hidden_size',
            'hidden_layers',
            'drop_rate',
        }

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type('Model')

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        result, msg = super(SimpleMLPBuildConfig, cls).validate_input(data, dtype, context)
        if not result:
            return result, msg
        _, values = context.pop()
        params: TDesc = values['params']
        for param in params.values():
            if not isinstance(param, int):
                return False, "One or more parameter(s) are not in the correct type."
        return True, None

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super(SimpleMLPBuildConfig, cls).create(data, tp, context, save)

    def build(self, context: ResourceContext, locked=False, parents_locked=False):
        model = SimpleMLP(
            num_classes=self.num_classes,
            input_size=self.input_size,
            hidden_size=self.hidden_size,
            hidden_layers=self.hidden_layers,
            drop_rate=self.drop_rate,
        )
        # noinspection PyArgumentList
        return self.target_type()(model)


# SimpleCNN builder
@MongoBuildConfig.register_build_config('SimpleCNN')
class SimpleCNNBuildConfig(MongoBuildConfig):

    # Fields
    num_classes = db.IntField(default=10)

    @classmethod
    def get_required(cls) -> set[str]:
        return set()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return {'num_classes'}

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type('Model')

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        result, msg = super().validate_input(data, dtype, context)
        if not result:
            return result, msg
        _, values = context.pop()
        params: TDesc = values['params']
        for param in params.values():
            if not isinstance(param, int):
                return False, "One or more parameter(s) are not in the correct type."
        return True, None

    @classmethod
    def create(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super(SimpleCNNBuildConfig, cls).create(data, dtype, context, save)

    def build(self, context: ResourceContext, locked=False, parents_locked=False):
        model = SimpleCNN(num_classes=self.num_classes)
        # noinspection PyArgumentList
        return self.target_type()(model)


# PNN builder
@MongoBuildConfig.register_build_config('PNN')
class PNNBuildConfig(MongoBuildConfig):
    
    _MLP = "mlp"
    _LINEAR = "linear"
    
    # Fields
    num_layers = db.IntField(default=1)
    in_features = db.IntField(default=784)
    hidden_features_per_column = db.IntField(default=100)
    adapter = db.StringField(choices=(_MLP, _LINEAR), default=_MLP)
    
    @classmethod
    def get_required(cls) -> set[str]:
        return set()
    
    @classmethod
    def get_optionals(cls) -> set[str]:
        return {
            'num_layers',
            'in_features',
            'hidden_features_per_column',
            'adapter',
        }

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type('Model')

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        result, msg = super().validate_input(data, dtype, context)
        if not result:
            return result, msg
        _, values = context.pop()
        params: TDesc = values['params']
        adapter = params.pop('adapter', cls._MLP)
        ok = isinstance(adapter, str)
        if ok:
            for param in params.values():
                if not isinstance(param, int):
                    ok = False
                    break
        if not ok:
            return False, "One or more parameter(s) are not in the correct type."
        return True, None

    @classmethod
    def create(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super(PNNBuildConfig, cls).create(data, dtype, context, save)

    def build(self, context: ResourceContext, locked=False, parents_locked=False):
        model = PNN(
            num_layers=self.num_layers,
            in_features=self.in_features,
            hidden_features_per_column=self.hidden_features_per_column,
            adapter=self.adapter,
        )
        # noinspection PyArgumentList
        return self.target_type()(model)


__all__ = [
    'SimpleMLPBuildConfig',
    'SimpleCNNBuildConfig',
    'PNNBuildConfig',
]