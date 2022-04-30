from mongoengine import ValidationError

from application.resources.datatypes import *
from application.mongo.resources.mongo_base_configs import *
from avalanche.evaluation.metrics import *


# Validator for standard metric helper settings
def std_name_validate(metric_cfg):
    try:
        for item in metric_cfg.items():
            if not isinstance(item[0], str):
                raise ValidationError(f"Unknown key type: '{type(item[0]).__name__}'")
            elif not isinstance(item[1], bool):
                raise ValidationError(f"Unknown value type: '{type(item[1]).__name__}'")
            elif not item[0] in StandardMetricSetBuildConfig.__values__:
                raise ValidationError("Unknown metric evaluation scope.")
    except Exception as ex:
        raise ValidationError(f"Error when validating document: '{ex}': '{ex.args[0]}'")


# Helper functions ONLY metricset builder
@MongoBuildConfig.register_build_config('StandardMetricSet')
class StandardMetricSetBuildConfig(MongoBuildConfig):
    """
    Build config for an Evaluation Plugin metrics set based ONLY on helper functions:
        accuracy_metrics
        loss_metrics
        bwt_metrics
        forgetting_metrics
        forward_transfer_metrics
        confusion_matrix_metrics
        cpu_usage_metrics
        disk_usage_metrics
        gpu_usage_metrics
        ram_usage_metrics
        timing_metrics
        MAC_metrics
        labels_repartition_metrics
        mean_scores_metrics
    """
    accuracy = db.MapField(db.BooleanField(), validation=std_name_validate)
    loss = db.MapField(db.BooleanField(), validation=std_name_validate)
    bwt = db.MapField(db.BooleanField(), validation=std_name_validate)
    forgetting = db.MapField(db.BooleanField(), validation=std_name_validate)
    forward_transfer = db.MapField(db.BooleanField(), validation=std_name_validate)
    confusion_matrix = db.MapField(db.BooleanField(), validation=std_name_validate)
    cpu_usage = db.MapField(db.BooleanField(), validation=std_name_validate)
    disk_usage = db.MapField(db.BooleanField(), validation=std_name_validate)
    gpu_usage = db.MapField(db.BooleanField(), validation=std_name_validate)
    ram_usage = db.MapField(db.BooleanField(), validation=std_name_validate)
    timing = db.MapField(db.BooleanField(), validation=std_name_validate)
    MAC = db.MapField(db.BooleanField(), validation=std_name_validate)
    labels_repartition = db.MapField(db.BooleanField(), validation=std_name_validate)
    mean_scores = db.MapField(db.BooleanField(), validation=std_name_validate)

    @classmethod
    def get_required(cls) -> set[str]:
        return set()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return {
            'accuracy',
            'loss',
            'bwt',
            'forgetting',
            'forward_transfer',
            'confusion_matrix',
            'cpu_usage',
            'disk_usage',
            'gpu_usage',
            'ram_usage',
            'timing',
            'MAC',
            'labels_repartition',
            'mean_scores',
        }

    @classmethod
    def has_extras(cls) -> bool:
        return False

    @classmethod
    def nullables(cls) -> set[str]:
        return set()

    __values__ = {
        'minibatch',
        'epoch',
        'epoch_running',
        'experience',
        'stream',
        'trained_experience',
    }

    @staticmethod
    def get_metrics_helper_name(name: str):
        if name in StandardMetricSetBuildConfig.names():
            return f"{name}_metrics"
        else:
            raise ValueError("Unknown metrics helper function.")

    @staticmethod
    def get_all_metrics_helper_names():
        result = []
        for name in StandardMetricSetBuildConfig.names():
            result.append(f"{name}_metrics")
        return result

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type("StandardMetricSet")

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        result, msg = super().validate_input(data, dtype, context)
        if not result:
            return result, msg
        # TODO Sostituire con la validazione sul dict preso dal context!
        actuals: TDesc = {}
        for name in cls.names():
            val = data.get(name)
            if val is not None:
                checked = True
                if not isinstance(val, dict):
                    checked = False
                else:
                    for item in val.items():
                        if not isinstance(item[0], str) or not isinstance(item[1], bool):
                            checked = False
                if not checked:
                    return False, "One or more metrics type are not in {<bool>: <string>} dict type."
                else:
                    actuals[name] = val
        return True, None

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super().create(data, tp, context, save)

    def build(self, context: ResourceContext):
        metrics = []
        for name in self.names():
            vals = dict(eval(f"self.{name}") or {})
            if len(vals) > 0:
                ms = eval(f"{self.get_metrics_helper_name(name)}")(**vals)
                metrics.append(ms)
        metrics = tuple(metrics)
        # noinspection PyArgumentList
        return self.target_type()(*metrics)

    def update(self, data, context: ResourceContext):
        pass

    def delete(self, context: ResourceContext):
        super().delete(context)