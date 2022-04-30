from application.resources.datatypes import *
from application.mongo.resources.mongo_base_configs import *
from avalanche.models import SimpleMLP


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

    __required__ = []

    __optionals__ = [
        'num_classes',
        'input_size',
        'hidden_size',
        'hidden_layers',
        'drop_rate',
    ]

    @staticmethod
    def names():
        return SimpleMLPBuildConfig.__required__ + \
               SimpleMLPBuildConfig.__optionals__

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type('Model')

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        if not all(fname in data for fname in cls.__required__):
            return False, "Missing one or more required parameter(s)."
        actuals: TDesc = {}
        for name in cls.names():
            val = data.get(name)
            if val is not None:
                if not isinstance(val, int):
                    return False, "One or more parameter(s) are not in the correct type."
                actuals[name] = val
            return True, None

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: ResourceContext, save: bool = True):
        if not cls.validate_input(data, tp, context):
            raise ValueError()
        actuals: TDesc = {}
        for name in cls.names():
            val = data.get(name)
            if val is not None:
                actuals[name] = val
        # noinspection PyArgumentList
        return cls(**actuals)

    def build(self, context: ResourceContext):
        model = SimpleMLP(
            num_classes=self.num_classes,
            input_size=self.input_size,
            hidden_size=self.hidden_size,
            hidden_layers=self.hidden_layers,
            drop_rate=self.drop_rate,
        )
        # noinspection PyArgumentList
        return self.target_type()(model)

    def update(self, data, context: ResourceContext):
        pass

    def delete(self, context: ResourceContext):
        super().delete(context)
