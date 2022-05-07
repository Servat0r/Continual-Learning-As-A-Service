from application.utils import get_device
from application.mongo.resources.mongo_base_configs import *
from application.mongo.resources.metricsets import *
from application.mongo.resources.criterions import *
from application.mongo.resources.optimizers import *
from application.mongo.resources.models import *

from avalanche.logging import CSVLogger, InteractiveLogger
from avalanche.training.plugins import EvaluationPlugin


class MongoBaseStrategyBuildConfig(MongoBuildConfig):
    """
    Base class template for strategies build configs.
    """
    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    model = db.ReferenceField(MongoModel.config_type(), required=True)
    optimizer = db.ReferenceField(MongoCLOptimizer.config_type(), required=True)     # TODO!
    criterion = db.ReferenceField(MongoCLCriterion.config_type(), required=True)     # TODO!
    train_mb_size = db.IntField(default=1)
    train_epochs = db.IntField(default=1)
    eval_mb_size = db.IntField(default=None)
    eval_every = db.IntField(default=-1)
    metricset = db.ReferenceField(MongoStandardMetricSet.config_type(), required=True)

    @staticmethod
    @abstractmethod
    def get_avalanche_strategy() -> t.Type[BaseStrategy]:
        pass

    @classmethod
    @abstractmethod
    def get_required(cls) -> set[str]:
        return {
            'model',
            'optimizer',
            'metricset',
        }

    @classmethod
    @abstractmethod
    def get_optionals(cls) -> set[str]:
        return {
            'criterion',
            'train_mb_size',
            'train_epochs',
            'eval_mb_size',
            'eval_every',
        }

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type('Strategy')

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: UserWorkspaceResourceContext) -> TBoolStr:
        result, msg = super().validate_input(data, dtype, context)
        if not result:
            return result, msg
        iname, values = context.pop()
        params: TDesc = values['params']

        train_mb_size = params.get('train_mb_size') or 0
        train_epochs = params.get('train_epochs') or 0
        eval_mb_size = params.get('eval_mb_size') or 0
        eval_every = params.get('eval_every') or -1
        int_check = all(isinstance(param, int) for param in {
            train_mb_size, train_epochs, eval_mb_size, eval_every,
        })
        if not int_check or eval_every < -1:
            return False, "One or more parameters are not in the correct type."

        model_name = params['model']
        optim_name = params['optimizer']
        criterion_name = params['criterion']
        metricset_name = params['metricset']

        owner = User.canonicalize(context.get_username())
        workspace = Workspace.canonicalize(context)

        model = MongoModel.config_type().get_one(owner, workspace, model_name)
        optim = MongoCLOptimizer.config_type().get_one(owner, workspace, optim_name)
        criterion = MongoCLCriterion.config_type().get_one(owner, workspace, criterion_name)
        metricset = MongoStandardMetricSet.config_type().get_one(owner, workspace, metricset_name)

        refs_check = all(res is not None for res in [model, optim, criterion, metricset])
        if not refs_check:
            return False, "One or more referred resource does not exist."
        else:
            params['model'] = model
            params['optimizer'] = optim
            params['criterion'] = criterion
            params['metricset'] = metricset
            context.push(iname, values)
            return True, None

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super().create(data, tp, context, save)

    def build(self, context: UserWorkspaceResourceContext):
        model = self.model.build(context)
        optim = self.optimizer.build(context)
        criterion = self.criterion.build(context)
        metricset = self.metricset.build(context)
        workspace = Workspace.canonicalize(context)

        # TODO Pass it from experiment! (From context?)
        log_folder = os.path.join(
            BaseDataManager.get().get_root(),
            *workspace.experiments_base_dir_parents(),
            workspace.experiments_base_dir(),
            'exp2',
            'logs',
        )

        strategy = self.get_avalanche_strategy()(
            model.get_value(), optim.get_value(),
            criterion.get_value(), device=get_device(),
            train_mb_size=self.train_mb_size, train_epochs=self.train_epochs,
            eval_mb_size=self.eval_mb_size, eval_every=self.eval_every,
            evaluator=EvaluationPlugin(
                *metricset.get_value(),
                loggers=[
                    CSVLogger(log_folder=log_folder),
                    InteractiveLogger(),
                ]
            ),
        )
        # noinspection PyArgumentList
        return self.target_type()(strategy)