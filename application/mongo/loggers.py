"""
Extended Avalanche loggers for interacting with data manager.
"""
import torch

from avalanche.evaluation.metric_results import MetricValue
from avalanche.logging import StrategyLogger

from application.utils import t
from application.data_managing.base import BaseDataManager

if t.TYPE_CHECKING:
    from avalanche.training import BaseStrategy


class ExtendedCSVLogger(StrategyLogger):
    """
    An extended CSVLogger that logs accuracy and loss metrics into customized
    training and eval results csv files and is compatible with data manager
    (i.e., it uses BaseDataManager file and directory API), thus synchronizing
    with general experiment data storage (e.g. in Workspaces directories on
    the local FileSystem).
    """

    _DFL_TRAIN_RESULTS_FILE_NAME = 'training_results.csv'
    _DFL_EVAL_RESULTS_FILE_NAME = 'eval_results.csv'

    def __init__(self, log_folder: list[str],
                 train_file_name: str = _DFL_TRAIN_RESULTS_FILE_NAME,
                 eval_file_name: str = _DFL_EVAL_RESULTS_FILE_NAME):

        super().__init__()

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
        self.val_acc, self.val_loss = 0, 0

        # create files
        self.manager.create_file((self.train_file_name, self.log_folder, None))
        self.manager.create_file((self.eval_file_name, self.log_folder, None))

        # print csv headers
        self.manager.print_to_file(self.train_file_name, self.log_folder,
                                   'training_exp', 'epoch', 'training_accuracy', 'val_accuracy',
                                   'training_loss', 'val_loss', sep=',', append=False, flush=True)
        self.manager.print_to_file(self.eval_file_name, self.log_folder,
                                   'eval_exp', 'training_exp', 'eval_accuracy', 'eval_loss',
                                   'forgetting', sep=',', append=False, flush=True)

    def log_single_metric(self, name, value, x_plot) -> None:
        pass

    def _val_to_str(self, m_val):
        if isinstance(m_val, torch.Tensor):
            return '\n' + str(m_val)
        elif isinstance(m_val, float):
            return f'{m_val:.4f}'
        else:
            return str(m_val)

    def print_train_metrics(self, training_exp, epoch, train_acc,
                            val_acc, train_loss, val_loss):
        if self.log_folder is None:
            raise RuntimeError("Undefined log folder.")
        self.manager.print_to_file(self.train_file_name, self.log_folder,
                                   training_exp, epoch, self._val_to_str(train_acc),
                                   self._val_to_str(val_acc), self._val_to_str(train_loss),
                                   self._val_to_str(val_loss), sep=',', append=True, flush=True)

    def print_eval_metrics(self, eval_exp, training_exp, eval_acc,
                           eval_loss, forgetting):
        if self.log_folder is None:
            raise RuntimeError("Undefined log folder.")
        self.manager.print_to_file(self.eval_file_name, self.log_folder,
                                   eval_exp, training_exp, self._val_to_str(eval_acc),
                                   self._val_to_str(eval_loss), self._val_to_str(forgetting),
                                   sep=',', append=True, flush=True)

    def after_training_epoch(self, strategy: 'BaseStrategy',
                             metric_values: t.List['MetricValue'], **kwargs):
        super().after_training_epoch(strategy, metric_values, **kwargs)
        train_acc, val_acc, train_loss, val_loss = 0, 0, 0, 0
        for val in metric_values:
            if 'train_stream' in val.name:
                if val.name.startswith('Top1_Acc_Epoch'):
                    train_acc = val.value
                elif val.name.startswith('Loss_Epoch'):
                    train_loss = val.value

        self.print_train_metrics(self.training_exp_id,
                                 strategy.clock.train_exp_epochs,
                                 train_acc, self.val_acc, train_loss,
                                 self.val_loss)

    def after_eval_exp(self, strategy: 'BaseStrategy',
                       metric_values: t.List['MetricValue'], **kwargs):
        super().after_eval_exp(strategy, metric_values, **kwargs)
        acc, loss, forgetting = 0, 0, 0

        for val in metric_values:
            if self.in_train_phase:  # validation within training
                if val.name.startswith('Top1_Acc_Exp'):
                    self.val_acc = val.value
                elif val.name.startswith('Loss_Exp'):
                    self.val_loss = val.value
            else:
                if val.name.startswith('Top1_Acc_Exp'):
                    acc = val.value
                elif val.name.startswith('Loss_Exp'):
                    loss = val.value
                elif val.name.startswith('ExperienceForgetting'):
                    forgetting = val.value

        if not self.in_train_phase:
            self.print_eval_metrics(strategy.experience.current_experience,
                                    self.training_exp_id, acc, loss,
                                    forgetting)

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

    def before_training(self, strategy: 'BaseStrategy',
                        metric_values: t.List['MetricValue'], **kwargs):
        self.in_train_phase = True

    def after_training(self, strategy: 'BaseStrategy',
                       metric_values: t.List['MetricValue'], **kwargs):
        self.in_train_phase = False

    def close(self):
        pass


__all__ = ['ExtendedCSVLogger']