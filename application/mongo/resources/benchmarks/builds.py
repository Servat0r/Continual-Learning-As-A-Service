from application.resources.datatypes import *
from application.mongo.resources.mongo_base_configs import *
from avalanche.benchmarks.classic import SplitMNIST


# SplitMNIST builder
@MongoBuildConfig.register_build_config('SplitMNIST')
class SplitMNISTBuildConfig(MongoBuildConfig):
    """
    Build config for a standard SplitMNIST benchmark based on avalanche.benchmarks.classics#SplitMNIST function.
    """

    __required__ = ['n_experiences']
    __optionals__ = [
        'return_task_id',
        'seed',
        'fixed_class_order',
        'shuffle',
        'dataset_root',
    ]

    n_experiences = db.IntField(required=True)
    return_task_id = db.BooleanField(required=False, default=False)
    seed = db.IntField(default=None)
    fixed_class_order = db.ListField(db.IntField(), default=None)
    shuffle = db.BooleanField(default=True)
    dataset_root = db.StringField(default=None)

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type('Benchmark')

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        if not all(fname in data for fname in cls.__required__):
            raise ValueError()
        n_experiences = data['n_experiences']
        return_task_id = data.get('return_task_id') or False
        seed = data.get('seed')
        fixed_class_order = data.get('fixed_class_order')
        shuffle = data.get('shuffle') or True
        dataset_root = data.get('dataset_root')
        result = isinstance(n_experiences, int) and \
            isinstance(return_task_id, bool) and \
            (isinstance(seed, int) or seed is None) and \
            (isinstance(fixed_class_order, list) or fixed_class_order is None) and \
            isinstance(shuffle, bool) and \
            (isinstance(dataset_root, str) or dataset_root is None)
        return result, None if result else "One or more parameter(s) is/are incorrect."

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: ResourceContext, save: bool = True):
        if not cls.validate_input(data, tp, context):
            raise ValueError()
        n_experiences = data['n_experiences']
        return_task_id = data.get('return_task_id') or False
        seed = data.get('seed')
        fixed_class_order = data.get('fixed_class_order')
        shuffle = data.get('shuffle') or True
        dataset_root = data.get('dataset_root')
        # noinspection PyArgumentList
        return cls(
            n_experiences=n_experiences,
            return_task_id=return_task_id,
            seed=seed,
            fixed_class_order=fixed_class_order,
            shuffle=shuffle,
            dataset_root=dataset_root,
        )

    def build(self, context: ResourceContext):
        benchmark = SplitMNIST(
            self.n_experiences,
            return_task_id=self.return_task_id,
            seed=self.seed,
            fixed_class_order=self.fixed_class_order,
            shuffle=self.shuffle,
            dataset_root=self.dataset_root,
        )
        # noinspection PyArgumentList
        return self.target_type()(benchmark)

    def update(self, data, context: ResourceContext):
        pass

    def delete(self, context: ResourceContext):
        super().delete(context)


# FashionMNIST builder