from __future__ import annotations

from torchvision.models import *

from application.utils import TBoolStr, t, TDesc, abstractmethod
from application.database import db

from application.resources.contexts import ResourceContext
from application.resources.base import DataType

from application.mongo.resources.mongo_base_configs import *


# Torchvision models builder
class BaseTorchVisionModelsBuildConfig(MongoBuildConfig):

    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    pretrained = db.BooleanField(default=False)

    def to_dict(self, links=True) -> TDesc:
        data = super().to_dict(links=links)
        data.update({'pretrained': self.pretrained})
        return data

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type('Model')

    @classmethod
    def get_required(cls) -> set[str]:
        return super(BaseTorchVisionModelsBuildConfig, cls).get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(BaseTorchVisionModelsBuildConfig, cls).get_optionals().union({'pretrained'})

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        result, msg = super(BaseTorchVisionModelsBuildConfig, cls).validate_input(data, dtype, context)
        if not result:
            return False, f"Failed to validate input: '{msg}'."
        _, values = context.head()
        params: TDesc = values['params']
        pretrained = params.get('pretrained', False)
        if not isinstance(pretrained, bool):
            return False, "Parameter 'pretrained' must be a boolean!"
        return True, None

    @classmethod
    def create(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super(BaseTorchVisionModelsBuildConfig, cls).create(data, dtype, context, save)

    @abstractmethod
    def get_torch_model_builder(self) -> t.Callable:
        pass

    def build(self, context: ResourceContext, locked=False, parents_locked=False):
        builder = self.get_torch_model_builder()
        model = builder(pretrained=self.pretrained)
        # noinspection PyArgumentList
        return self.target_type()(model)


class SingleParamTorchVisionModelsBuildConfig(BaseTorchVisionModelsBuildConfig):

    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    @staticmethod
    @abstractmethod
    def param_type() -> type:
        pass

    @staticmethod
    @abstractmethod
    def maps() -> dict[t.Any, t.Callable]:
        pass

    @staticmethod
    @abstractmethod
    def default_val() -> t.Any:
        pass

    def to_dict(self, links=True) -> TDesc:
        data = super().to_dict(links=links)
        data.update({'net_id': self.net_id})
        return data

    @classmethod
    def get_required(cls) -> set[str]:
        return super(SingleParamTorchVisionModelsBuildConfig, cls).get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(SingleParamTorchVisionModelsBuildConfig, cls).get_optionals().union({'net_id'})

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        result, msg = super(SingleParamTorchVisionModelsBuildConfig, cls).validate_input(data, dtype, context)
        if not result:
            return False, f"Failed to validate input: '{msg}'"
        _, values = context.pop()
        params = values['params']
        net_id = params.get('net_id', cls.default_val())
        if not isinstance(net_id, cls.param_type()):
            return False, "Parameter 'net_id' must be an integer!"
        elif net_id not in cls.maps().keys():
            return False, f"Parameter 'net_id' must be a value inside in {cls.maps().keys()}"
        return True, None

    @classmethod
    def create(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super(SingleParamTorchVisionModelsBuildConfig, cls).create(data, dtype, context, save)

    def get_torch_model_builder(self) -> t.Callable:
        return self.maps().get(self.net_id, self.default_val())


# AlexNet
@MongoBuildConfig.register_build_config('AlexNet')
class AlexNetBuildConfig(BaseTorchVisionModelsBuildConfig):

    def get_torch_model_builder(self) -> t.Callable:
        return alexnet


# ResNets
@MongoBuildConfig.register_build_config('ResNet')
class ResNetBuildConfig(SingleParamTorchVisionModelsBuildConfig):

    # Fields
    net_id = db.IntField(default=18)

    @staticmethod
    def param_type() -> type:
        return int

    @staticmethod
    def default_val() -> int:
        return 18

    @staticmethod
    def maps() -> dict[int, t.Callable]:
        return {
            18: resnet18,
            34: resnet34,
            50: resnet50,
            101: resnet101,
            152: resnet152,
        }

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        return super(ResNetBuildConfig, cls).validate_input(data, dtype, context)

    @classmethod
    def create(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super(ResNetBuildConfig, cls).create(data, dtype, context, save)


@MongoBuildConfig.register_build_config('SqueezeNet')
class SqueezeNetBuildConfig(BaseTorchVisionModelsBuildConfig):

    def get_torch_model_builder(self) -> t.Callable:
        return squeezenet1_0


@MongoBuildConfig.register_build_config('DenseNet')
class DenseNetBuildConfig(SingleParamTorchVisionModelsBuildConfig):

    # Fields
    net_id = db.IntField(default=121)

    @staticmethod
    def param_type() -> type:
        return int

    @staticmethod
    def default_val() -> int:
        return 121

    @staticmethod
    def maps() -> dict[int, t.Callable]:
        return {
            121: densenet121,
            161: densenet161,
            169: densenet169,
            201: densenet201,
        }

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        return super(DenseNetBuildConfig, cls).validate_input(data, dtype, context)

    @classmethod
    def create(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super(DenseNetBuildConfig, cls).create(data, dtype, context, save)


@MongoBuildConfig.register_build_config('GoogleNet')
class GoogleNetBuildConfig(BaseTorchVisionModelsBuildConfig):

    def get_torch_model_builder(self) -> t.Callable:
        return googlenet


@MongoBuildConfig.register_build_config('MobileNet')
class MobileNetBuildConfig(SingleParamTorchVisionModelsBuildConfig):

    # Fields
    net_id = db.StringField(default='v2')

    @staticmethod
    def default_val() -> str:
        return 'v2'

    @staticmethod
    def param_type() -> type:
        return str

    @staticmethod
    def maps() -> dict[t.Any, t.Callable]:
        return {
            'v2': mobilenet_v2,
            'v3_small': mobilenet_v3_small,
            'v3_large': mobilenet_v3_large,
        }


@MongoBuildConfig.register_build_config('EfficientNet')
class EfficientNetBuildConfig(SingleParamTorchVisionModelsBuildConfig):

    # Fields
    net_id = db.StringField(default='b0')
    __cached_maps = None

    @staticmethod
    def param_type() -> type:
        return str

    @staticmethod
    def default_val() -> t.Any:
        return 'b0'

    @staticmethod
    def maps() -> dict[t.Any, t.Callable]:
        if EfficientNetBuildConfig.__cached_maps is None:
            __cached_maps = {
                f'b{i}': eval(f'efficientnet_b{i}') for i in range(0, 8)
            }
        else:
            return EfficientNetBuildConfig.__cached_maps


@MongoBuildConfig.register_build_config('RegNet')
class RegNetBuildConfig(SingleParamTorchVisionModelsBuildConfig):

    # Fields
    net_id = db.StringField(default='x_8gf')

    @staticmethod
    def param_type() -> type:
        return str
    
    @staticmethod
    def default_val() -> str:
        return 'x_8gf'
    
    @staticmethod
    def maps() -> dict[t.Any, t.Callable]:
        return {
            'y_400mf': regnet_y_400mf,
            'y_800mf': regnet_y_800mf,
            'y_1_6gf': regnet_y_1_6gf,
            'y_3_2gf': regnet_y_3_2gf,
            'y_8gf': regnet_y_8gf,
            'y_16gf': regnet_y_16gf,
            'y_32gf': regnet_y_32gf,
            'y_128gf': regnet_y_128gf,
            'x_400mf': regnet_x_400mf,
            'x_800mf': regnet_x_800mf,
            'x_1_6gf': regnet_x_1_6gf,
            'x_3_2gf': regnet_x_3_2gf,
            'x_8gf': regnet_x_8gf,
            'x_16gf': regnet_x_16gf,
            'x_32gf': regnet_x_32gf,
        }


@MongoBuildConfig.register_build_config('ConvNext')
class ConvNextBuildConfig(SingleParamTorchVisionModelsBuildConfig):

    # Fields
    net_id = db.StringField(default='base')

    @staticmethod
    def param_type() -> type:
        return str

    @staticmethod
    def default_val() -> t.Any:
        return 'base'

    @staticmethod
    def maps() -> dict[t.Any, t.Callable]:
        return {
            'tiny': convnext_tiny,
            'small': convnext_small,
            'base': convnext_base,
            'large': convnext_large,
        }


__all__ = [
    'AlexNetBuildConfig',
    'ResNetBuildConfig',
    'SqueezeNetBuildConfig',
    'GoogleNetBuildConfig',
    'DenseNetBuildConfig',
    'MobileNetBuildConfig',
    'EfficientNetBuildConfig',
    'RegNetBuildConfig',
    'ConvNextBuildConfig',
]