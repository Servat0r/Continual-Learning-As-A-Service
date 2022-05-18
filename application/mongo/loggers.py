"""
Extended Avalanche loggers for interacting with data manager.
"""
from __future__ import annotations
import torch

from avalanche.evaluation.metric_results import MetricValue
from avalanche.logging import StrategyLogger

from application.utils import t
from application.data_managing.base import BaseDataManager
from application.resources import StandardMetricSet

if t.TYPE_CHECKING:
    from avalanche.training import BaseStrategy


class ExtendedCSVLogger(StrategyLogger):
    """
    An extended CSVLogger that most of the implemented metrics into customized
    training and eval results csv files and is compatible with data manager
    (i.e., it uses BaseDataManager file and directory API), thus synchronizing
    with general experiment data storage (e.g. in Workspaces directories on
    the local FileSystem).
    """

    _DFL_TRAIN_RESULTS_FILE_NAME = 'train_results.csv'
    _DFL_EVAL_RESULTS_FILE_NAME = 'eval_results.csv'

    # noinspection PyUnusedLocal
    @staticmethod
    def mnames_translations(gpu_id: int = 0, **kwargs):
        return {
            'accuracy': {
                'minibatch': 'Top1_Acc_MB',
                'epoch': 'Top1_Acc_Epoch',
                'experience': 'Top1_Acc_Exp',
                'stream': 'Top1_Acc_Stream',
            },
            'loss': {
                'minibatch': "Loss_MB",
                'epoch': "Loss_Epoch",
                'experience': "Loss_Exp",
                'stream': "Loss_Stream",
            },
            'forgetting': {
                'experience': "ExperienceForgetting",
                'stream': "StreamForgetting",
            },

            'timing': {
                'minibatch': "Time_MB",
                'epoch': "Time_Epoch",
                'experience': "Time_Exp",
                'stream': "Time_Stream",
            },
            'ram_usage': {
                'minibatch': "MaxRAMUsage_MB",
                'epoch': "MaxRAMUsage_Epoch",
                'experience': "MaxRAMUsage_Exp",
                'stream': "MaxRAMUsage_Stream",
            },
            'cpu_usage': {
                'minibatch': "CPUUsage_MB",
                'epoch': "CPUUsage_Epoch",
                'experience': "CPUUsage_Exp",
                'stream': "CPUUsage_Stream",
            },
            'disk_usage': {
                'minibatch': "DiskUsage_MB",
                'epoch': "DiskUsage_Epoch",
                'experience': "DiskUsage_Exp",
                'stream': "DiskUsage_Stream",
            },
            'gpu_usage': {
                'minibatch': f"MaxGPU{gpu_id}Usage_MB",
                'epoch': f"MaxGPU{gpu_id}Usage_Epoch",
                'experience': f"MaxGPU{gpu_id}Usage_Experience",
                'stream': f"MaxGPU{gpu_id}Usage_Stream",
            },

            'bwt': {
                'experience': "ExperienceBWT",
                'stream': "StreamBWT",
            },
            'forward_transfer': {
                'experience': "ExperienceForwardTransfer",
                'stream': "StreamForwardTransfer",
            },
            'MAC': {
                'minibatch': "MAC_MB",
                'epoch': "MAC_Epoch",
                'experience': "MAC_Exp",
            },
        }

    _MNAMES_ORDER: list[str] = [
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
    ]

    @staticmethod
    def _mnames_order(names: list[str]) -> list[str]:
        mnames_list = ExtendedCSVLogger._MNAMES_ORDER
        canonical: list[str | None] = len(mnames_list) * [None]
        extras: list[str] = []

        for i in range(len(names)):
            name = names[i]
            try:
                idx = mnames_list.index(name)
                canonical[idx] = name
            except ValueError:
                extras.append(name)

        result: list[str] = []
        for i in range(len(canonical)):
            name = canonical[i]
            if name is not None:
                result.append(name)
        result += extras
        return result

    def __init__(
        self, log_folder: list[str], metricset: StandardMetricSet,
        train_file_name: str = _DFL_TRAIN_RESULTS_FILE_NAME,
        eval_file_name: str = _DFL_EVAL_RESULTS_FILE_NAME,
    ):

        super().__init__()

        self.metric_names = self._mnames_order(metricset.get_metric_names())
        self.val_dict = {k: 0 for k in self.metric_names}

        self.train_file_name = train_file_name
        self.eval_file_name = eval_file_name
        self.log_folder = log_folder
        self.manager = BaseDataManager.get()
        # current training experience id
        self.training_exp_id = None

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
        for name in self.metric_names:
            train_headers.append(f"training_{name}")
            train_headers.append(f"val_{name}")

        eval_headers: list[str] = [f"eval_{name}" for name in self.metric_names]

        self.manager.print_to_file(self.train_file_name, self.log_folder,
                                   'training_exp', 'epoch', *train_headers,
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
        # train_acc, val_acc, train_loss, val_loss, train_cpu, val_cpu, train_disk, val_disk, train_ram, val_ram):
        if self.log_folder is None:
            raise RuntimeError("Undefined log folder.")
        values = [self._val_to_str(m_val) for m_val in values]
        self.manager.print_to_file(
            self.train_file_name, self.log_folder,
            training_exp, epoch, *values,
            # self._val_to_str(train_acc),
            # self._val_to_str(val_acc), # self._val_to_str(train_loss),
            # self._val_to_str(val_loss), # self._val_to_str(train_cpu),
            # self._val_to_str(val_cpu), # self._val_to_str(train_disk),
            # self._val_to_str(val_disk), # self._val_to_str(train_ram),
            # self._val_to_str(val_ram),
            sep=',', append=True, flush=True,
        )

    def print_eval_metrics(self, eval_exp, training_exp, *values):
        # eval_acc, eval_loss, forgetting, eval_cpu, eval_disk, eval_ram):
        if self.log_folder is None:
            raise RuntimeError("Undefined log folder.")
        values = [self._val_to_str(m_val) for m_val in values]
        self.manager.print_to_file(
            self.eval_file_name, self.log_folder,
            eval_exp, training_exp, *values,
            # self._val_to_str(eval_acc),
            # self._val_to_str(eval_loss), self._val_to_str(forgetting),
            # self._val_to_str(eval_cpu), self._val_to_str(eval_disk),
            # self._val_to_str(eval_ram),
            sep=',', append=True, flush=True,
        )

    def after_training_epoch(self, strategy: 'BaseStrategy',
                             metric_values: t.List['MetricValue'], **kwargs):
        super().after_training_epoch(strategy, metric_values, **kwargs)
        # train_acc, val_acc, train_loss, val_loss = 0, 0, 0, 0
        # train_cpu, val_cpu, train_disk, val_disk, train_ram, val_ram = 0, 0, 0, 0, 0, 0

        mtype = 'epoch'
        vals_to_print: list[int | float] = []

        for name in self.metric_names:
            current_value = 0
            val_start = self.mnames_translations().get(name).get(mtype)
            if val_start is not None:
                for val in metric_values:
                    if val.name.startswith(val_start):
                        current_value = val.value
                        break
            val_current_value = self.val_dict.get(name, 0)
            vals_to_print += [current_value, val_current_value]
        
        self.print_train_metrics(
            self.training_exp_id, strategy.clock.train_exp_epochs, *vals_to_print,
        )

    def after_eval_exp(self, strategy: 'BaseStrategy',
                       metric_values: t.List['MetricValue'], **kwargs):
        super().after_eval_exp(strategy, metric_values, **kwargs)
        # acc, loss, forgetting, cpu, disk, ram = 0, 0, 0, 0, 0, 0

        mtype = 'experience'
        vals_to_print: list[int | float] = []
        
        for name in self.metric_names:
            current_value = 0
            val_start = self.mnames_translations().get(name).get(mtype)
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
                # acc, loss, forgetting, cpu, disk, ram
            )

    def before_training_exp(self, strategy: 'BaseStrategy',
                            metric_values: t.List['MetricValue'], **kwargs):
        super().before_training(strategy, metric_values, **kwargs)
        self.training_exp_id = strategy.experience.current_experience

    def before_eval(self, strategy: 'BaseStrategy',
                    metric_values: t.List['MetricValue'], **kwargs):
        """
        Manage the case in which `eval` is first called before `train`
        """
        if self.in_train_phase is None:
            self.in_train_phase = False
        print("BEFORE EVAL", *metric_values, sep='\n')

    def before_training(self, strategy: 'BaseStrategy',
                        metric_values: t.List['MetricValue'], **kwargs):
        self.in_train_phase = True
        print("BEFORE TRAINING", *metric_values, sep='\n')

    def after_training(self, strategy: 'BaseStrategy',
                       metric_values: t.List['MetricValue'], **kwargs):
        self.in_train_phase = False
        print("AFTER TRAINING", *metric_values, sep='\n')

    def close(self):
        pass


__all__ = ['ExtendedCSVLogger']