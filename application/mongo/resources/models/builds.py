from __future__ import annotations

import schema as sch

from avalanche.models.simple_mlp import SimpleMLP
from avalanche.models.simple_cnn import SimpleCNN
from avalanche.models.pnn import PNN

from application.utils import TBoolStr, t, TDesc, abstractmethod
from application.database import db
from application.avalanche_ext import *

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
    drop_rate = db.FloatField(default=0.0)

    def to_dict(self, links=True) -> TDesc:
        data = super().to_dict(links=links)
        data.update({
            'num_classes': self.num_classes,
            'input_size': self.input_size,
            'hidden_size': self.hidden_size,
            'hidden_layers': self.hidden_layers,
            'drop_rate': self.drop_rate,
        })
        return data

    @classmethod
    def schema_dict(cls) -> dict:
        result = super(SimpleMLPBuildConfig, cls).schema_dict()
        result.update({
            sch.Optional('num_classes'): int,
            sch.Optional('input_size'): int,
            sch.Optional('hidden_size'): int,
            sch.Optional('hidden_layers'): int,
            sch.Optional('drop_rate'): float,
        })
        return result

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
        return super(SimpleMLPBuildConfig, cls).validate_input(data, dtype, context)

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

    def to_dict(self, links=True) -> TDesc:
        data = super().to_dict(links=links)
        data.update({'num_classes': self.num_classes})
        return data

    @classmethod
    def schema_dict(cls) -> dict:
        result = super(SimpleCNNBuildConfig, cls).schema_dict()
        result.update({
            sch.Optional('num_classes'): int,
        })
        return result

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
        return super().validate_input(data, dtype, context)

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
    
    def to_dict(self, links=True) -> TDesc:
        data = super().to_dict(links=links)
        data.update({
            'num_layers': self.num_layers,
            'in_features': self.in_features,
            'hidden_features_per_column': self.hidden_features_per_column,
            'adapter': self.adapter,
        })
        return data
    
    @classmethod
    def schema_dict(cls) -> dict:
        result = super(PNNBuildConfig, cls).schema_dict()
        result.update({
            sch.Optional('num_layers'): int,
            sch.Optional('in_features'): int,
            sch.Optional('hidden_features_per_column'): int,
            sch.Optional('adapter'): sch.And(str, lambda x: x in (cls._MLP, cls._LINEAR)),
        })
        return result

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
        return super().validate_input(data, dtype, context)

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


# avalanche_ext models
# MLP builder
@MongoBuildConfig.register_build_config('MLP')
class MLPBuildConfig(MongoBuildConfig):
    """Build config for the MLP as defined in application.avalanche_ext.models.commons.py."""

    # Fields
    input_size = db.IntField(default=28*28)
    hidden_size = db.IntField(default=256)
    hidden_layers = db.IntField(default=2)
    output_size = db.IntField(default=10)
    drop_rate = db.FloatField(default=0.0)
    relu_act = db.BooleanField(default=True)

    def to_dict(self, links=True) -> TDesc:
        data = super().to_dict(links=links)
        data.update({
            'input_size': self.input_size,
            'hidden_size': self.hidden_size,
            'hidden_layers': self.hidden_layers,
            'output_size': self.output_size,
            'drop_rate': self.drop_rate,
            'relu_act': self.relu_act,
        })
        return data

    @classmethod
    def schema_dict(cls) -> dict:
        data = super().schema_dict()
        data.update({
            sch.Optional('input_size'): int,
            sch.Optional('hidden_size'): int,
            sch.Optional('hidden_layers'): int,
            sch.Optional('output_size'): int,
            sch.Optional('drop_rate'): float,
            sch.Optional('relu_act'): bool,
        })
        return data

    @classmethod
    def get_required(cls) -> set[str]:
        return set()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return {
            'input_size',
            'hidden_size',
            'hidden_layers',
            'output_size',
            'drop_rate',
            'relu_act',
        }

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type('Model')

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        return super().validate_input(data, dtype, context)

    @classmethod
    def create(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super(MLPBuildConfig, cls).create(data, dtype, context, save)

    def build(self, context: ResourceContext, locked=False, parents_locked=False):
        model = MLP(
            input_size=self.input_size,
            hidden_size=self.hidden_size,
            hidden_layers=self.hidden_layers,
            output_size=self.output_size,
            drop_rate=self.drop_rate,
            relu_act=self.relu_act,
        )
        # noinspection PyArgumentList
        return self.target_type()(model)


# MultiHeadMLP builder
@MongoBuildConfig.register_build_config('MultiHeadMLP')
class MultiHeadMLPBuildConfig(MongoBuildConfig):
    """Build config for the MultiHeadMLP as defined in application.avalanche_ext.models.commons.py."""

    # Fields
    input_size = db.IntField(default=28*28)
    hidden_size = db.IntField(default=256)
    hidden_layers = db.IntField(default=2)
    drop_rate = db.FloatField(default=0.0)
    relu_act = db.BooleanField(default=True)

    def to_dict(self, links=True) -> TDesc:
        data = super().to_dict(links=links)
        data.update({
            'input_size': self.input_size,
            'hidden_size': self.hidden_size,
            'hidden_layers': self.hidden_layers,
            'drop_rate': self.drop_rate,
            'relu_act': self.relu_act,
        })
        return data

    @classmethod
    def schema_dict(cls) -> dict:
        data = super().schema_dict()
        data.update({
            sch.Optional('input_size'): int,
            sch.Optional('hidden_size'): int,
            sch.Optional('hidden_layers'): int,
            sch.Optional('drop_rate', default=0.0): float,
            sch.Optional('relu_act', default=True): bool,
        })
        return data

    @classmethod
    def get_required(cls) -> set[str]:
        return set()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return {
            'input_size',
            'hidden_size',
            'hidden_layers',
            'drop_rate',
            'relu_act',
        }

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type('Model')

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        return super().validate_input(data, dtype, context)

    @classmethod
    def create(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super(MultiHeadMLPBuildConfig, cls).create(data, dtype, context, save)

    def build(self, context: ResourceContext, locked=False, parents_locked=False):
        model = MultiHeadMLP(
            input_size=self.input_size,
            hidden_size=self.hidden_size,
            hidden_layers=self.hidden_layers,
            drop_rate=self.drop_rate,
            relu_act=self.relu_act,
        )
        # noinspection PyArgumentList
        return self.target_type()(model)


# SI_CNN builder
@MongoBuildConfig.register_build_config('SI_CNN')
class SynapticIntelligenceCNNBuildConfig(MongoBuildConfig):

    # Fields
    hidden_size = db.IntField(default=512)

    def to_dict(self, links=True) -> TDesc:
        data = super().to_dict(links=links)
        data.update({'hidden_size': self.hidden_size})
        return data

    @classmethod
    def schema_dict(cls) -> dict:
        data = super().schema_dict()
        data.update({
            sch.Optional('hidden_size'): int,
        })
        return data

    @classmethod
    def get_required(cls) -> set[str]:
        return set()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return {'hidden_size'}

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type('Model')

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        return super(SynapticIntelligenceCNNBuildConfig, cls).validate_input(data, dtype, context)

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super(SynapticIntelligenceCNNBuildConfig, cls).create(data, tp, context, save)

    def build(self, context: ResourceContext, locked=False, parents_locked=False):
        model = SI_CNN(hidden_size=self.hidden_size)
        # noinspection PyArgumentList
        return self.target_type()(model)


# VGGSmall builder
@MongoBuildConfig.register_build_config('VGGSmall')
class VGGSmallBuildConfig(MongoBuildConfig):

    def to_dict(self, links=True) -> TDesc:
        return super().to_dict(links=links)

    @classmethod
    def get_required(cls) -> set[str]:
        return super(VGGSmallBuildConfig, cls).get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(VGGSmallBuildConfig, cls).get_optionals()

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type('Model')

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        return super(VGGSmallBuildConfig, cls).validate_input(data, dtype, context)

    @classmethod
    def create(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super(VGGSmallBuildConfig, cls).create(data, dtype, context, save)

    def build(self, context: ResourceContext, locked=False, parents_locked=False):
        model = VGGSmall()
        # noinspection PyArgumentList
        return self.target_type()(model)


# MultiHeadVGGClassifier builder
@MongoBuildConfig.register_build_config('MultiHeadVGGClassifier')
class MultiHeadVGGClassifierBuildConfig(MongoBuildConfig):

    # Fields
    in_features = db.IntField(required=True)
    n_classes = db.IntField(required=True)

    def to_dict(self, links=True) -> TDesc:
        data = super().to_dict(links=links)
        data.update({
            'in_features': self.in_features,
            'n_classes': self.n_classes,
        })
        return data

    @classmethod
    def schema_dict(cls) -> dict:
        data = super().schema_dict()
        data.update({
            'in_features': int,
            'n_classes': int,
        })
        return data

    @classmethod
    def get_required(cls) -> set[str]:
        return super(MultiHeadVGGClassifierBuildConfig, cls).get_required().union({'in_features', 'n_classes'})

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(MultiHeadVGGClassifierBuildConfig, cls).get_optionals()

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type('Model')

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        return super(MultiHeadVGGClassifierBuildConfig, cls).validate_input(data, dtype, context)

    @classmethod
    def create(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super(MultiHeadVGGClassifierBuildConfig, cls).create(data, dtype, context, save)

    def build(self, context: ResourceContext, locked=False, parents_locked=False):
        model = MultiHeadVGGClassifier(self.in_features, self.n_classes)
        # noinspection PyArgumentList
        return self.target_type()(model)


# MultiHeadVGGSmall builder
@MongoBuildConfig.register_build_config('MultiHeadVGGSmall')
class MultiHeadVGGSmallBuildConfig(MongoBuildConfig):
    
    n_classes = db.IntField(default=20)

    def to_dict(self, links=True) -> TDesc:
        data = super().to_dict(links=links)
        data.update({'n_classes': self.n_classes})
        return data

    @classmethod
    def schema_dict(cls) -> dict:
        data = super().schema_dict()
        data.update({
            sch.Optional('n_classes'): int,
        })
        return data

    @classmethod
    def get_required(cls) -> set[str]:
        return super(MultiHeadVGGSmallBuildConfig, cls).get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(MultiHeadVGGSmallBuildConfig, cls).get_optionals().union({'n_classes'})

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type('Model')

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        return super(MultiHeadVGGSmallBuildConfig, cls).validate_input(data, dtype, context)

    @classmethod
    def create(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super(MultiHeadVGGSmallBuildConfig, cls).create(data, dtype, context, save)

    def build(self, context: ResourceContext, locked=False, parents_locked=False):
        model = MultiHeadVGGSmall(self.n_classes)
        # noinspection PyArgumentList
        return self.target_type()(model)


__all__ = [
    'SimpleMLPBuildConfig',
    'SimpleCNNBuildConfig',
    'PNNBuildConfig',

    'MLPBuildConfig',
    'MultiHeadMLPBuildConfig',
    'SynapticIntelligenceCNNBuildConfig',

    'VGGSmallBuildConfig',
    'MultiHeadVGGClassifierBuildConfig',
    'MultiHeadVGGSmall',
]