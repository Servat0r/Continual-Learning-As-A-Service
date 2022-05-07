from application.utils import get_device
from application.mongo.resources.mongo_base_configs import *
from application.mongo.resources.metricsets import *
from application.mongo.resources.criterions import *
from application.mongo.resources.optimizers import *
from application.mongo.resources.models import *
from avalanche.training.strategies import Naive, Cumulative, SynapticIntelligence
from .base_builds import *


# Naive strategy builder
@MongoBuildConfig.register_build_config('Naive')
class NaiveBuildConfig(MongoBaseStrategyBuildConfig):
    """
    Build config for Naive strategy.
    """
    @staticmethod
    def get_avalanche_strategy() -> t.Type[BaseStrategy]:
        return Naive

    @classmethod
    def get_required(cls) -> set[str]:
        return super().get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super().get_optionals()


# Cumulative strategy builder
@MongoBuildConfig.register_build_config('Cumulative')
class CumulativeBuildConfig(MongoBaseStrategyBuildConfig):

    @staticmethod
    def get_avalanche_strategy() -> t.Type[BaseStrategy]:
        return Cumulative

    @classmethod
    def get_required(cls) -> set[str]:
        return super().get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super().get_optionals()


# Synaptic Intelligence strategy builder
@MongoBuildConfig.register_build_config('SynapticIntelligence')
class SynapticIntelligenceBuildConfig(MongoBaseStrategyBuildConfig):

    # Fields
    si_lambda = db.ListField(db.FloatField(), required=True)
    eps = db.FloatField(default=0.0000001)

    @staticmethod
    def get_avalanche_strategy() -> t.Type[BaseStrategy]:
        return SynapticIntelligence

    @classmethod
    def get_required(cls) -> set[str]:
        return super().get_required().union({'si_lambda'})

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super().get_optionals().union({'eps'})

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: UserWorkspaceResourceContext) -> TBoolStr:
        result, msg = super().validate_input(data, dtype, context)
        if not result:
            return result, msg

        iname, values = context.pop()
        params: TDesc = values['params']
        si_lambda = params['si_lambda']
        eps = params.get('eps') or 0.0000001

        si_checked = True
        if isinstance(si_lambda, list):
            for si_l in si_lambda:
                if not isinstance(si_l, float):
                    si_checked = False
                    break
        else:
            si_checked = False
        if not si_checked:
            return False, "Parameter 'si_lambda' is not of the correct type."

        if not isinstance(eps, float):
            return False, "Parameter 'eps' is not of the correct type."

        context.push(iname, values)
        return True, None

    def build(self, context: UserWorkspaceResourceContext):
        model = self.model.build(context)
        optim = self.optimizer.build(context)
        criterion = self.criterion.build(context)
        metricset = self.metricset.build(context)

        strategy = SynapticIntelligence(
            model.get_value(), optim.get_value(), criterion.get_value(),
            si_lambda=self.si_lambda, eps=self.eps, device=get_device(),
            train_mb_size=self.train_mb_size, train_epochs=self.train_epochs,
            eval_mb_size=self.eval_mb_size, eval_every=self.eval_every,
            # TODO Evaluator!
        )
        # noinspection PyArgumentList
        return self.target_type()(strategy)