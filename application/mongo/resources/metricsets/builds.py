from __future__ import annotations
from mongoengine import ValidationError as MongoEngineValidationError

from application.utils import TBoolStr, t, TDesc
from application.database import db

from application.resources.contexts import ResourceContext
from application.resources.base import DataType

from application.mongo.resources.mongo_base_configs import *


# Validator for standard metric helper settings
def std_name_validate(metric_cfg):
    try:
        for item in metric_cfg.items():
            if not isinstance(item[0], str):
                raise MongoEngineValidationError(f"Unknown key type: '{type(item[0]).__name__}'")
            elif not isinstance(item[1], bool):
                raise MongoEngineValidationError(f"Unknown value type: '{type(item[1]).__name__}'")
            elif not item[0] in StandardMetricSetBuildConfig.__values__:
                raise MongoEngineValidationError("Unknown metric evaluation scope.")
    except Exception as ex:
        raise MongoEngineValidationError(f"Error when validating document: '{ex}': '{ex.args[0]}'")


# Helper functions ONLY metricset builder
@MongoBuildConfig.register_build_config('StandardMetricSet')
class StandardMetricSetBuildConfig(MongoBuildConfig):
    """
    Build config for an Evaluation Plugin metrics set based ONLY on helper functions:
        accuracy_metrics
        loss_metrics
        forgetting_metrics

        timing_metrics
        ram_usage_metrics
        cpu_usage_metrics
        disk_usage_metrics
        gpu_usage_metrics

        bwt_metrics
        forward_transfer_metrics
        MAC_metrics

    JSON request format is of the type:
    {
        <metric_name>: {
            "minibatch": true/false,
            "epoch": true/false,
            "experience": true/false,
            "stream": true/false,
            "train_time": true/false,
            "eval_time": true/false
        }
    }
    """
    accuracy = db.MapField(db.BooleanField(), validation=std_name_validate, default={})
    loss = db.MapField(db.BooleanField(), validation=std_name_validate, default={})
    forgetting = db.MapField(db.BooleanField(), validation=std_name_validate, default={})

    timing = db.MapField(db.BooleanField(), validation=std_name_validate, default={})
    ram_usage = db.MapField(db.BooleanField(), validation=std_name_validate, default={})
    cpu_usage = db.MapField(db.BooleanField(), validation=std_name_validate, default={})
    disk_usage = db.MapField(db.BooleanField(), validation=std_name_validate, default={})
    gpu_usage = db.MapField(db.BooleanField(), validation=std_name_validate, default={})

    bwt = db.MapField(db.BooleanField(), validation=std_name_validate, default={})
    forward_transfer = db.MapField(db.BooleanField(), validation=std_name_validate, default={})
    MAC = db.MapField(db.BooleanField(), validation=std_name_validate, default={})

    @classmethod
    def get_required(cls) -> set[str]:
        return set()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return {
            'accuracy',
            'loss',
            'forgetting',

            'timing',
            'ram_usage',
            'cpu_usage',
            'disk_usage',
            'gpu_usage',

            'bwt',
            'forward_transfer',
            'MAC',
        }

    __values__ = {
        'minibatch',
        'epoch',
        'epoch_running',
        'experience',
        'stream',
        'trained_experience',
        'train_time',
        'eval_time',
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

        _, values = context.pop()
        params = values['params']
        for param in params.values():
            checked = True
            if not isinstance(param, dict):
                checked = False
            else:
                for item in param.items():
                    if not isinstance(item[0], str) or not isinstance(item[1], bool):
                        checked = False
                        break
            if not checked:
                return False, "One or more metrics types are not in {<string>: <bool>} dict type."
        return True, None

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: ResourceContext, save: bool = True):
        ok, bc_name, params, extras = cls._filter_data(data)
        # noinspection PyArgumentList
        return cls(**params)

    def build(self, context: ResourceContext, locked=False, parents_locked=False):
        metrics = []
        metric_names: dict[str, list[str]] = {'train': [], 'eval': []}
        for name in self.names():
            vals = dict(eval(f"self.{name}") or {})
            if len(vals) > 0:
                train_time: bool = vals.get('train_time')
                eval_time: bool = vals.get('eval_time')

                if train_time is None and eval_time is None:
                    train_time = True
                    eval_time = True
                else:
                    train_time = False if train_time is None else vals.pop('train_time')
                    eval_time = False if eval_time is None else vals.pop('eval_time')

                ms = eval(f"{self.get_metrics_helper_name(name)}")(**vals)
                metrics.append(ms)
                if train_time:
                    metric_names['train'].append(name)
                if eval_time:
                    metric_names['eval'].append(name)
        metrics = tuple(metrics)
        # noinspection PyArgumentList
        return self.target_type()(metric_names, *metrics)


__all__ = [
    'std_name_validate',
    'StandardMetricSetBuildConfig',
]