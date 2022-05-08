from __future__ import annotations
from torch.nn.modules import CrossEntropyLoss

from application.utils import TBoolStr, t, TDesc

from application.resources.contexts import ResourceContext
from application.resources.base import DataType

from application.mongo.resources.mongo_base_configs import *


# CrossEntropyLoss
@MongoBuildConfig.register_build_config('CrossEntropyLoss')
class CrossEntropyLossBuildConfig(MongoBuildConfig):

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

    def build(self, context: ResourceContext):
        criterion = CrossEntropyLoss()
        # noinspection PyArgumentList
        return self.target_type()(criterion)


__all__ = ['CrossEntropyLossBuildConfig']