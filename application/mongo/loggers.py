"""
Extended Avalanche loggers for interacting with data manager.
"""
from __future__ import annotations
import torch

from avalanche.evaluation.metric_results import MetricValue
from avalanche.logging import BaseLogger
from avalanche.core import SupervisedPlugin

from application.utils import t
from application.data_managing.base import BaseDataManager
from application.resources import StandardMetricSet
from application.mongo.utils import mnames_order_filter, mnames_translations

if t.TYPE_CHECKING:
    from avalanche.training.templates import SupervisedTemplate


class ExtendedCSVLogger(BaseLogger, SupervisedPlugin):
    """
    An extended CSVLogger that most of the implemented metrics into customized
    training and eval results csv files and is compatible with data manager
    (i.e., it uses BaseDataManager file and directory API), thus synchronizing
    with general experiment data storage (e.g. in Workspaces directories on
    the local FileSystem).
    """

    _DFL_TRAIN_RESULTS_FILE_NAME = 'train_results.csv'
    _DFL_EVAL_RESULTS_FILE_NAME = 'eval_results.csv'

    def __init__(
        self, log_folder: list[str], metricset: StandardMetricSet,
        train_file_name: str = _DFL_TRAIN_RESULTS_FILE_NAME,
        eval_file_name: str = _DFL_EVAL_RESULTS_FILE_NAME,
    ):

        super().__init__()

        self.metric_names = {k: mnames_order_filter(v) for k, v in metricset.get_metric_names().items()}
        self.val_dict = {k: 0 for k in self.metric_names}

        self.train_file_name = train_file_name
        self.eval_file_name = eval_file_name
        self.log_folder = log_folder
        self.manager = BaseDataManager.get()
        # current training experience id
        self.training_exp_id = None
        # current training epoch id
        self.training_epoch_id = None
        # current eval experience id
        self.eval_experience_id = None
        # current training experience #patterns
        self.current_n_patterns = None

        # if we are currently training or evaluating
        # evaluation within training will not change this flag
        self.in_train_phase = None

        # validation metrics computed during training
        self.val_acc, self.val_loss, self.val_cpu, self.val_disk, self.val_ram = 0, 0, 0, 0, 0

        # create files
        self.manager.create_file((self.train_file_name, self.log_folder, None))
        self.manager.create_file((self.eval_file_name, self.log_folder, None))

        # print csv headers
        train_headers: list[str] = []
        for name in self.metric_names['train']:
            train_headers.append(f"training_{name}")
            train_headers.append(f"val_{name}")

        eval_headers: list[str] = [f"eval_{name}" for name in self.metric_names['eval']]

        self.manager.print_to_file(self.train_file_name, self.log_folder,
                                   'training_exp', 'epoch', 'training_items', *train_headers,
                                   sep=',', append=False, flush=True)

        self.manager.print_to_file(self.eval_file_name, self.log_folder,
                                   'eval_exp', 'training_exp', *eval_headers,
                                   sep=',', append=False, flush=True)

    def log_single_metric(self, name, value, x_plot) -> None:
        pass

    @staticmethod
    def _val_to_str(m_val):
        if isinstance(m_val, torch.Tensor):
            return '\n' + str(m_val)
        elif isinstance(m_val, float):
            return f'{m_val:.4f}'
        else:
            return str(m_val)

    def print_train_metrics(self, training_exp, epoch, *values):
        if self.log_folder is None:
            raise RuntimeError("Undefined log folder.")
        values = [self._val_to_str(m_val) for m_val in values]
        self.manager.print_to_file(
            self.train_file_name, self.log_folder,
            training_exp, epoch, self.current_n_patterns, *values,
            sep=',', append=True, flush=True,
        )

    def print_eval_metrics(self, eval_exp, training_exp, *values):
        if self.log_folder is None:
            raise RuntimeError("Undefined log folder.")
        values = [self._val_to_str(m_val) for m_val in values]
        self.manager.print_to_file(
            self.eval_file_name, self.log_folder,
            eval_exp, training_exp, *values,
            sep=',', append=True, flush=True,
        )

    def after_train_dataset_adaptation(self, strategy: "SupervisedTemplate", *args, **kwargs):
        self.current_n_patterns = len(strategy.adapted_dataset)

    # noinspection PyMethodOverriding
    def before_training_epoch(self, strategy: "SupervisedTemplate", metric_values: t.List["MetricValue"], **kwargs):
        self.current_n_patterns = len(strategy.adapted_dataset)
        print(f"Starting training on experience = {self.training_exp_id}, epoch = {self.training_epoch_id})")

    # noinspection PyMethodOverriding
    def after_training_epoch(self, strategy: "SupervisedTemplate",
                             metric_values: t.List["MetricValue"], **kwargs):
        super().after_training_epoch(strategy, metric_values, **kwargs)
        mtype = 'epoch'
        vals_to_print: list[int | float] = []

        for name in self.metric_names['train']:
            current_value = -1
            val_start = mnames_translations().get(name).get(mtype)
            if val_start is not None:
                for val in metric_values:
                    if val.name.startswith(val_start):
                        current_value = val.value
                        break
            val_current_value = self.val_dict.get(name, -1)
            vals_to_print += [current_value, val_current_value]
        
        self.print_train_metrics(
            self.training_exp_id, strategy.clock.train_exp_epochs, *vals_to_print,
        )
        print(f"Ended training on experience = {self.training_exp_id}, epoch = {self.training_epoch_id})")
        self.training_epoch_id += 1

    # noinspection PyMethodOverriding
    def before_eval_exp(self, strategy: 'SupervisedTemplate', metric_values: t.List['MetricValue'], **kwargs):
        super().before_eval_exp(strategy, metric_values, **kwargs)
        print(f"Starting evaluating on experience = {strategy.experience.current_experience} of {self.training_exp_id}")

    # noinspection PyMethodOverriding
    def after_eval_exp(self, strategy: 'SupervisedTemplate',
                       metric_values: t.List['MetricValue'], **kwargs):
        super().after_eval_exp(strategy, metric_values, **kwargs)
        mtype = 'experience'
        vals_to_print: list[int | float] = []
        
        for name in self.metric_names['eval']:
            current_value = -1
            val_start = mnames_translations().get(name).get(mtype)
            if val_start is not None:
                for val in metric_values:
                    if val.name.startswith(val_start):
                        current_value = val.value
                        break
            if self.in_train_phase:
                self.val_dict[name] = current_value
            else:
                vals_to_print.append(current_value)

        if not self.in_train_phase:
            self.print_eval_metrics(
                strategy.experience.current_experience,
                self.training_exp_id, *vals_to_print,
            )
            print(
                f"Ended evaluating on experience = {strategy.experience.current_experience} of {self.training_exp_id}"
            )

    # noinspection PyMethodOverriding
    def before_training_exp(self, strategy: 'SupervisedTemplate',
                            metric_values: t.List['MetricValue'], **kwargs):
        super().before_training(strategy, metric_values, **kwargs)
        self.training_exp_id = strategy.experience.current_experience
        self.training_epoch_id = 0

    # noinspection PyMethodOverriding
    def before_eval(self, strategy: 'SupervisedTemplate',
                    metric_values: t.List['MetricValue'], **kwargs):
        """
        Manage the case in which `eval` is first called before `train`
        """
        if self.in_train_phase is None:
            self.in_train_phase = False
        print("BEFORE EVAL", *metric_values, sep='\n')

    # noinspection PyMethodOverriding
    def before_training(self, strategy: 'SupervisedTemplate',
                        metric_values: t.List['MetricValue'], **kwargs):
        self.in_train_phase = True
        print("BEFORE TRAINING", *metric_values, sep='\n')

    # noinspection PyMethodOverriding
    def after_training(self, strategy: 'SupervisedTemplate',
                       metric_values: t.List['MetricValue'], **kwargs):
        self.in_train_phase = False
        print("AFTER TRAINING", *metric_values, sep='\n')

    def close(self):
        pass


__all__ = ['ExtendedCSVLogger']