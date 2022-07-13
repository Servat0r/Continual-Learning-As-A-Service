from __future__ import annotations

import schema as sch
from torch.nn.modules import CrossEntropyLoss, MSELoss

from application.utils import TBoolStr, t, TDesc
from application.database import *

from application.resources.contexts import ResourceContext
from application.resources.base import DataType

from application.mongo.resources.mongo_base_configs import *


# CrossEntropyLoss
@MongoBuildConfig.register_build_config('CrossEntropyLoss')
class CrossEntropyLossBuildConfig(MongoBuildConfig):

    def to_dict(self, links=True) -> TDesc:
        return super().to_dict(links=links)

    @classmethod
    def schema_dict(cls) -> dict:
        return super(CrossEntropyLossBuildConfig, cls).schema_dict()

    @classmethod
    def get_required(cls) -> set[str]:
        return set()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return set()

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type("CLCriterion")

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        return super().validate_input(data, dtype, context)

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super().create(data, tp, context, save)

    def build(self, context: ResourceContext, locked=False, parents_locked=False):
        criterion = CrossEntropyLoss()
        # noinspection PyArgumentList
        return self.target_type()(criterion)


# MeanSquareLoss
@MongoBuildConfig.register_build_config('MSELoss')
class MSELossBuildConfig(MongoBuildConfig):

    __choices = ['none', 'mean', 'sum']
    __default = 'mean'

    @staticmethod
    def choices() -> list[str]:
        return ['none', 'mean', 'sum']

    @staticmethod
    def default_val() -> str:
        return 'mean'

    # Fields
    reduction = db.StringField(choices=__choices, default=__default)

    @classmethod
    def schema_dict(cls) -> dict:
        result = super(MSELossBuildConfig, cls).schema_dict()
        result.update({
            sch.Optional('reduction', default=cls.default_val()): sch.And(str, lambda x: x in cls.choices()),
        })
        return result

    def to_dict(self, links=True) -> TDesc:
        data = super().to_dict(links=links)
        data.update({'reduction': self.reduction})
        return data

    @classmethod
    def get_required(cls) -> set[str]:
        return super(MSELossBuildConfig, cls).get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(MSELossBuildConfig, cls).get_optionals().union({'reduction'})

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type("CLCriterion")

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        return super(MSELossBuildConfig, cls).validate_input(data, dtype, context)

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super().create(data, tp, context, save)

    def build(self, context: ResourceContext, locked=False, parents_locked=False):
        criterion = MSELoss(reduction=self.reduction)
        # noinspection PyArgumentList
        return self.target_type()(criterion)


__all__ = [
    'CrossEntropyLossBuildConfig',
    'MSELossBuildConfig',
]