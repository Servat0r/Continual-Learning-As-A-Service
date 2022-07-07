# Embedded Build Configs for dataset transforms
from __future__ import annotations

import io
from PIL import Image

from torchvision.transforms import ToTensor, CenterCrop, Normalize, Compose, \
    RandomCrop, RandomHorizontalFlip

from application.utils import TBoolStr, TDesc, abstractmethod, t
from application.database import db
from application.resources.contexts import ResourceContext
from application.mongo.resources.mongo_base_configs import *


class TransformConfig(MongoEmbeddedBuildConfig):

    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    __CONFIGS__: TDesc = {}

    @staticmethod
    def register_transform_config(name: str = None):
        def registerer(cls):
            nonlocal name
            if name is None:
                name = cls.__name__
            TransformConfig.__CONFIGS__[name] = cls
            return cls

        return registerer

    @classmethod
    def get_by_name(cls, name: str | TDesc):
        if isinstance(name, str):
            return cls.__CONFIGS__.get(name)
        elif isinstance(name, dict):
            cname = name.get('name')
            if cname is None:
                raise ValueError('Missing name')
            else:
                return cls.__CONFIGS__.get(cname)

    @classmethod
    def get_required(cls) -> set[str]:
        return super(TransformConfig, cls).get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(TransformConfig, cls).get_optionals()

    @abstractmethod
    def get_transform(self):
        pass

    @classmethod
    @abstractmethod
    def validate_input(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        return super(TransformConfig, cls).validate_input(data, context)

    @classmethod
    @abstractmethod
    def create(cls, data: TDesc, context: ResourceContext, save: bool = True):
        return super(TransformConfig, cls).create(data, context, save)


# Special transforms for converting bytes to PIL Image(s)
class BytesToPIL:

    def __call__(self, image_bytes):
        img = Image.open(io.BytesIO(image_bytes))
        return img


class BytesToRGB:

    def __call__(self, image_bytes):
        return Image.open(io.BytesIO(image_bytes)).convert('RGB')


class BytesToGrayscale:

    def __call__(self, image_bytes):
        return Image.open(io.BytesIO(image_bytes)).convert('L')


@TransformConfig.register_transform_config('BytesToPIL')
class BytesToPILConfig(TransformConfig):

    @classmethod
    def get_required(cls) -> set[str]:
        return set()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return set()

    @classmethod
    def validate_input(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        result, msg = super(BytesToPILConfig, cls).validate_input(data, context)
        context.pop()
        return result, msg

    @classmethod
    def create(cls, data: TDesc, context: ResourceContext, save: bool = True):
        return super(BytesToPILConfig, cls).create(data, context, save)

    def to_dict(self, links=True) -> TDesc:
        return {
            'name': 'BytesToPIL',
        }

    def get_transform(self):
        return BytesToPIL()


@TransformConfig.register_transform_config('BytesToRGB')
class BytesToRGBConfig(TransformConfig):

    @classmethod
    def get_required(cls) -> set[str]:
        return set()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return set()

    @classmethod
    def validate_input(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        result, msg = super(BytesToRGBConfig, cls).validate_input(data, context)
        context.pop()
        return result, msg

    @classmethod
    def create(cls, data: TDesc, context: ResourceContext, save: bool = True):
        return super(BytesToRGBConfig, cls).create(data, context, save)

    def to_dict(self, links=True) -> TDesc:
        return {
            'name': 'BytesToRGB',
        }

    def get_transform(self):
        return BytesToRGB()


@TransformConfig.register_transform_config('BytesToGrayscale')
class BytesToGrayscaleConfig(TransformConfig):

    @classmethod
    def get_required(cls) -> set[str]:
        return set()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return set()

    @classmethod
    def validate_input(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        result, msg = super(BytesToGrayscaleConfig, cls).validate_input(data, context)
        context.pop()
        return result, msg

    @classmethod
    def create(cls, data: TDesc, context: ResourceContext, save: bool = True):
        return super(BytesToGrayscaleConfig, cls).create(data, context, save)

    def to_dict(self, links=True) -> TDesc:
        return {
            'name': 'BytesToGrayscale',
        }

    def get_transform(self):
        return BytesToGrayscale()


# Common transforms
@TransformConfig.register_transform_config('ToTensor')
class ToTensorConfig(TransformConfig):

    @classmethod
    def get_required(cls) -> set[str]:
        return set()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return set()

    @classmethod
    def validate_input(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        result, msg = super(ToTensorConfig, cls).validate_input(data, context)
        context.pop()
        return result, msg

    @classmethod
    def create(cls, data: TDesc, context: ResourceContext, save: bool = True):
        return super(ToTensorConfig, cls).create(data, context, save)

    def to_dict(self, links=True) -> TDesc:
        return {
            'name': 'ToTensor',
        }

    def get_transform(self):
        return ToTensor()


@TransformConfig.register_transform_config('CenterCrop')
class CenterCropConfig(TransformConfig):

    width = db.IntField(required=True)
    height = db.IntField(required=True)

    def to_dict(self, links=True) -> TDesc:
        return {
            'name': 'CenterCrop',
            'width': self.width,
            'height': self.height,
        }

    @classmethod
    def get_required(cls) -> set[str]:
        return super(CenterCropConfig, cls).get_required().union({'width', 'height'})

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(CenterCropConfig, cls).get_optionals()

    @classmethod
    def validate_input(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        result, msg = super(CenterCropConfig, cls).validate_input(data, context)
        if not result:
            return result, msg
        _, values = context.pop()
        params = values['params']
        width = params['width']
        height = params['height']
        if not all(isinstance(val, int) for val in (width, height)):
            return False, "One or more parameter(s) is/are not of the correct type."
        return True, None

    @classmethod
    def create(cls, data: TDesc, context: ResourceContext, save: bool = True):
        return super(CenterCropConfig, cls).create(data, context, save)

    def get_transform(self):
        return CenterCrop([self.width, self.height])


@TransformConfig.register_transform_config('RandomCrop')
class RandomCropConfig(TransformConfig):

    # Fields
    width = db.IntField(required=True)
    height = db.IntField(required=True)
    padding = db.ListField(db.IntField(), default=None)
    pad_if_needed = db.BooleanField(default=False)
    fill = db.IntField(default=0)

    def to_dict(self, links=True) -> TDesc:
        return {
            'name': 'RandomCrop',
            'width': self.width,
            'height': self.height,
            'padding': self.padding,
            'pad_if_needed': self.pad_if_needed,
            'fill': self.fill,
        }

    @classmethod
    def get_required(cls) -> set[str]:
        return super(RandomCropConfig, cls).get_required().union({'width', 'height'})

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(RandomCropConfig, cls).get_optionals().union({'padding', 'pad_if_needed', 'fill'})

    @classmethod
    def validate_input(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        result, msg = super(RandomCropConfig, cls).validate_input(data, context)
        if not result:
            return result, msg
        _, values = context.pop()
        params = values['params']

        width = params['width']
        height = params['height']
        padding = params.get('padding', [])
        pad_if_needed = params.get('pad_if_needed', False)
        fill = params.get('fill', 0)

        all_int = all(isinstance(val, int) for val in (width, height, fill))
        all_bool = all(isinstance(val, bool) for val in (pad_if_needed,))
        check_padding = False
        if isinstance(padding, list):
            check_padding = all(isinstance(val, int) for val in padding)

        if not all_int and all_bool and check_padding:
            return False, "One or more parameter(s) is/are not of the correct type."
        return True, None

    @classmethod
    def create(cls, data: TDesc, context: ResourceContext, save: bool = True):
        return super(RandomCropConfig, cls).create(data, context, save)

    def get_transform(self):
        return RandomCrop(
            size=(self.height, self.width),
            padding=self.padding,
            pad_if_needed=self.pad_if_needed,
            fill=self.fill,
        )


@TransformConfig.register_transform_config('RandomHorizontalFlip')
class RandomHorizontalFlipConfig(TransformConfig):

    # Fields
    p = db.FloatField(default=0.5)

    def to_dict(self, links=True) -> TDesc:
        return {
            'name': 'RandomHorizontalFlip',
            'p': self.p,
        }

    @classmethod
    def get_required(cls) -> set[str]:
        return super(RandomHorizontalFlipConfig, cls).get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(RandomHorizontalFlipConfig, cls).get_optionals().union({'p'})

    @classmethod
    def validate_input(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        result, msg = super(RandomHorizontalFlipConfig, cls).validate_input(data, context)
        if not result:
            return False, msg
        iname, values = context.pop()
        params: TDesc = values['params']
        p = params.get('p', 0.5)
        result = isinstance(p, float)
        return result, (None if result else "Parameter 'p' is not of the correct type!")

    @classmethod
    def create(cls, data: TDesc, context: ResourceContext, save: bool = True):
        return super(RandomHorizontalFlipConfig, cls).create(data, context, save)

    def get_transform(self):
        return RandomHorizontalFlip(p=self.p)


@TransformConfig.register_transform_config('Normalize')
class NormalizeConfig(TransformConfig):

    # Fields
    mean = db.ListField(db.FloatField(), required=True)
    std = db.ListField(db.FloatField(), required=True)
    inplace = db.BooleanField(default=False)

    def to_dict(self, links=True) -> TDesc:
        return {
            'name': 'Normalize',
            'mean': self.mean,
            'std': self.std,
            'inplace': self.inplace,
        }

    @classmethod
    def get_required(cls) -> set[str]:
        return super(NormalizeConfig, cls).get_required().union({'mean', 'std'})

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(NormalizeConfig, cls).get_optionals().union({'inplace'})

    @classmethod
    def validate_input(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        result, msg = super(NormalizeConfig, cls).validate_input(data, context)
        if not result:
            return result, msg
        _, values = context.pop()
        params = values['params']
        mean = params['mean']
        std = params['std']
        inplace = params.get('inplace', False)
        
        check_mean = False
        if isinstance(mean, list):
            check_mean = all(isinstance(val, float) for val in mean)
        
        check_std = False
        if isinstance(std, list):
            check_std = all(isinstance(val, float) for val in std)
        
        if not check_mean and check_std and isinstance(inplace, bool):
            return False, "One or more parameter(s) is/are not of the correct type."
        return True, None

    @classmethod
    def create(cls, data: TDesc, context: ResourceContext, save: bool = True):
        return super(NormalizeConfig, cls).create(data, context, save)

    def get_transform(self):
        return Normalize(self.mean, self.std, self.inplace)


@TransformConfig.register_transform_config('Compose')
class ComposeConfig(TransformConfig):

    """
    Syntax:
    {
        "transforms": [
            {
                <transform_data>
            },
            {
                <transform_data>
            },
            ...
        ]
    }
    """

    transforms = db.ListField(db.EmbeddedDocumentField(TransformConfig), required=True)

    def to_dict(self, links=True) -> TDesc:
        return {
            'name': 'Compose',
            'transforms': [transform.to_dict(links=False) for transform in self.transforms],
        }

    @classmethod
    def get_required(cls) -> set[str]:
        return super(ComposeConfig, cls).get_required().union({'transforms'})

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(ComposeConfig, cls).get_optionals()

    @classmethod
    def validate_input(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        result, msg = super(ComposeConfig, cls).validate_input(data, context)
        if not result:
            return result, msg
        _, values = context.pop()
        params = values['params']
        transforms = params['transforms']
        if not isinstance(transforms, list):
            return False, "'transforms' parameter must be a list!"
        for transform_data in transforms:
            current_transform_config: t.Type[TransformConfig] = TransformConfig.get_by_name(transform_data)
            if current_transform_config is None:
                return False, "One or more list items lack transform name or the given transform does not exist."
            result, msg = current_transform_config.validate_input(transform_data, context)
            if not result:
                return False, f"One or more list items are not correct: '{msg}'."
        return True, None

    @classmethod
    def create(cls, data: TDesc, context: ResourceContext, save: bool = True):
        transforms_data = data['transforms']
        transforms = []
        for transform_data in transforms_data:
            transform_config: t.Type[TransformConfig] = TransformConfig.get_by_name(transform_data)
            if transform_config is None:
                raise RuntimeError(f"Unknown or not given transform config: '{transform_data.get('name')}'.")
            transform = transform_config.create(transform_data, context, save)
            if transform is None:
                raise RuntimeError(f"Failed to build transform from data: '{transform_data}'.")
            transforms.append(transform)
        data['transforms'] = transforms
        return super(ComposeConfig, cls).create(data, context, save)

    def get_transform(self):
        transforms = []
        for transform_config in self.transforms:
            transforms.append(transform_config.get_transform())
        return Compose(transforms)


# MNIST transforms
@TransformConfig.register_transform_config('TrainMNIST')
class DefaultMNISTTrainTransformConfig(TransformConfig):

    def to_dict(self, links=True) -> TDesc:
        return {
            'name': 'TrainMNIST',
        }

    @classmethod
    def get_required(cls) -> set[str]:
        return set()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return set()

    @classmethod
    def validate_input(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        result, msg = super(DefaultMNISTTrainTransformConfig, cls).validate_input(data, context)
        context.pop()
        return result, msg

    @classmethod
    def create(cls, data: TDesc, context: ResourceContext, save: bool = True):
        return super(DefaultMNISTTrainTransformConfig, cls).create(data, context, save)

    def get_transform(self):
        return Compose([ToTensor(), Normalize((0.1307,), (0.3081,))])


@TransformConfig.register_transform_config('EvalMNIST')
class DefaultMNISTEvalTransformConfig(TransformConfig):

    def to_dict(self, links=True) -> TDesc:
        return {
            'name': 'EvalMNIST',
        }

    @classmethod
    def get_required(cls) -> set[str]:
        return set()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return set()

    @classmethod
    def validate_input(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        result, msg = super(DefaultMNISTEvalTransformConfig, cls).validate_input(data, context)
        context.pop()
        return result, msg

    @classmethod
    def create(cls, data: TDesc, context: ResourceContext, save: bool = True):
        return super(DefaultMNISTEvalTransformConfig, cls).create(data, context, save)

    def get_transform(self):
        return Compose([ToTensor(), Normalize((0.1307,), (0.3081,))])


# CIFAR10 transforms
@TransformConfig.register_transform_config('TrainCIFAR10')
class DefaultCIFAR10TrainTransformConfig(TransformConfig):

    def to_dict(self, links=True) -> TDesc:
        return {
            'name': 'TrainCIFAR10',
        }

    @classmethod
    def get_required(cls) -> set[str]:
        return set()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return set()

    @classmethod
    def validate_input(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        result, msg = super(DefaultCIFAR10TrainTransformConfig, cls).validate_input(data, context)
        context.pop()
        return result, msg

    @classmethod
    def create(cls, data: TDesc, context: ResourceContext, save: bool = True):
        return super(DefaultCIFAR10TrainTransformConfig, cls).create(data, context, save)

    def get_transform(self):
        return Compose(
            [
                RandomCrop(32, padding=4),
                RandomHorizontalFlip(),
                ToTensor(),
                Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
            ]
        )


@TransformConfig.register_transform_config('EvalCIFAR10')
class DefaultCIFAR10EvalTransformConfig(TransformConfig):

    def to_dict(self, links=True) -> TDesc:
        return {
            'name': 'EvalCIFAR10',
        }

    @classmethod
    def get_required(cls) -> set[str]:
        return set()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return set()

    @classmethod
    def validate_input(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        result, msg = super(DefaultCIFAR10EvalTransformConfig, cls).validate_input(data, context)
        context.pop()
        return result, msg

    @classmethod
    def create(cls, data: TDesc, context: ResourceContext, save: bool = True):
        return super(DefaultCIFAR10EvalTransformConfig, cls).create(data, context, save)

    def get_transform(self):
        return Compose(
            [
                ToTensor(),
                Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
            ]
        )


# CIFAR100 transforms
@TransformConfig.register_transform_config('TrainCIFAR100')
class DefaultCIFAR100TrainTransformConfig(TransformConfig):

    def to_dict(self, links=True) -> TDesc:
        return {
            'name': 'TrainCIFAR100',
        }

    @classmethod
    def get_required(cls) -> set[str]:
        return set()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return set()

    @classmethod
    def validate_input(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        result, msg = super(DefaultCIFAR100TrainTransformConfig, cls).validate_input(data, context)
        context.pop()
        return result, msg

    @classmethod
    def create(cls, data: TDesc, context: ResourceContext, save: bool = True):
        return super(DefaultCIFAR100TrainTransformConfig, cls).create(data, context, save)

    def get_transform(self):
        return Compose(
            [
                RandomCrop(32, padding=4),
                RandomHorizontalFlip(),
                ToTensor(),
                Normalize((0.5071, 0.4865, 0.4409), (0.2673, 0.2564, 0.2762)),
            ]
        )


@TransformConfig.register_transform_config('EvalCIFAR100')
class DefaultCIFAR100EvalTransformConfig(TransformConfig):

    def to_dict(self, links=True) -> TDesc:
        return {
            'name': 'EvalCIFAR100',
        }

    @classmethod
    def get_required(cls) -> set[str]:
        return set()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return set()

    @classmethod
    def validate_input(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        result, msg = super(DefaultCIFAR100EvalTransformConfig, cls).validate_input(data, context)
        context.pop()
        return result, msg

    @classmethod
    def create(cls, data: TDesc, context: ResourceContext, save: bool = True):
        return super(DefaultCIFAR100EvalTransformConfig, cls).create(data, context, save)

    def get_transform(self):
        return Compose(
            [
                ToTensor(),
                Normalize((0.5071, 0.4865, 0.4409), (0.2673, 0.2564, 0.2762)),
            ]
        )


# CORe50 transforms
@TransformConfig.register_transform_config('TrainCORe50')
class DefaultCORe50TrainTransformConfig(TransformConfig):

    def to_dict(self, links=True) -> TDesc:
        return {
            'name': 'TrainCORe50',
        }

    @classmethod
    def get_required(cls) -> set[str]:
        return set()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return set()

    @classmethod
    def validate_input(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        result, msg = super(DefaultCORe50TrainTransformConfig, cls).validate_input(data, context)
        context.pop()
        return result, msg

    @classmethod
    def create(cls, data: TDesc, context: ResourceContext, save: bool = True):
        return super(DefaultCORe50TrainTransformConfig, cls).create(data, context, save)

    def get_transform(self):
        return Compose([
            ToTensor(),
            RandomHorizontalFlip(),
            Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])


@TransformConfig.register_transform_config('EvalCORe50')
class DefaultCORe50EvalTransformConfig(TransformConfig):

    def to_dict(self, links=True) -> TDesc:
        return {
            'name': 'EvalCORe50',
        }

    @classmethod
    def get_required(cls) -> set[str]:
        return set()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return set()

    @classmethod
    def validate_input(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        result, msg = super(DefaultCORe50EvalTransformConfig, cls).validate_input(data, context)
        context.pop()
        return result, msg

    @classmethod
    def create(cls, data: TDesc, context: ResourceContext, save: bool = True):
        return super(DefaultCORe50EvalTransformConfig, cls).create(data, context, save)

    def get_transform(self):
        return Compose([
            ToTensor(),
            Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])


# Tiny ImageNet transforms
@TransformConfig.register_transform_config('TrainTinyImageNet')
class DefaultTinyImageNetTrainTransformConfig(TransformConfig):

    def to_dict(self, links=True) -> TDesc:
        return {
            'name': 'TrainTinyImageNet',
        }

    @classmethod
    def get_required(cls) -> set[str]:
        return set()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return set()

    @classmethod
    def validate_input(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        result, msg = super(DefaultTinyImageNetTrainTransformConfig, cls).validate_input(data, context)
        context.pop()
        return result, msg

    @classmethod
    def create(cls, data: TDesc, context: ResourceContext, save: bool = True):
        return super(DefaultTinyImageNetTrainTransformConfig, cls).create(data, context, save)

    def get_transform(self):
        return Compose(
            [
                RandomHorizontalFlip(),
                ToTensor(),
                Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
            ]
        )


@TransformConfig.register_transform_config('EvalTinyImageNet')
class DefaultTinyImageNetEvalTransformConfig(TransformConfig):

    def to_dict(self, links=True) -> TDesc:
        return {
            'name': 'EvalTinyImageNet',
        }

    @classmethod
    def get_required(cls) -> set[str]:
        return set()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return set()

    @classmethod
    def validate_input(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        result, msg = super(DefaultTinyImageNetEvalTransformConfig, cls).validate_input(data, context)
        context.pop()
        return result, msg

    @classmethod
    def create(cls, data: TDesc, context: ResourceContext, save: bool = True):
        return super(DefaultTinyImageNetEvalTransformConfig, cls).create(data, context, save)

    def get_transform(self):
        return Compose(
            [
                ToTensor(),
                Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
            ]
        )


__all__ = [
    # extra transform(s)
    'BytesToPIL',
    'BytesToRGB',
    'BytesToGrayscale',

    # Transform Configs
    'TransformConfig',

    'BytesToPILConfig',
    'BytesToRGBConfig',
    'BytesToGrayscaleConfig',

    'ToTensorConfig',
    'CenterCropConfig',
    'RandomCropConfig',

    'RandomHorizontalFlipConfig',
    'NormalizeConfig',
    'ComposeConfig',

    'DefaultMNISTTrainTransformConfig',
    'DefaultMNISTEvalTransformConfig',

    'DefaultCIFAR10TrainTransformConfig',
    'DefaultCIFAR10EvalTransformConfig',

    'DefaultCIFAR100TrainTransformConfig',
    'DefaultCIFAR100EvalTransformConfig',

    'DefaultCORe50TrainTransformConfig',
    'DefaultCORe50EvalTransformConfig',

    'DefaultTinyImageNetTrainTransformConfig',
    'DefaultTinyImageNetEvalTransformConfig',
]