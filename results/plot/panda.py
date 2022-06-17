# Playing with pandas
from __future__ import annotations
import os
import pandas as pd
from matplotlib import pyplot as plt


print(os.getcwd())
dir_path = os.path.join('..', 'file_based_split_mnist_4_epochs', '0', 'naive', 'csv')
train_file_path = os.path.join(dir_path, 'train_results.csv')
eval_file_path = os.path.join(dir_path, 'eval_results.csv')


"""
Experience  TrainingItems   TrainingTiming  EvalAccuracy    EvalForgetting
0           12665           
0           12665
0           12665
"""


class AClass:
    """
    Given a dict of 'curve_name' ('Naive', 'Cumulative', ...) -> files, extracts the data from given files and returns
    a dict of 'curve_name' -> dataframe.
    """

    COLUMNS = ['Experience', 'TrainingItems', 'TrainingTiming', 'EvalAccuracy', 'EvalForgetting']

    def __init__(self, strategy_name: str, train_files: list[str], eval_files: list[str], compute_std=False):
        self.strategy_name = strategy_name
        self.train_files = train_files
        self.eval_files = eval_files
        self.compute_std = compute_std
        self.train_frames: list[pd.DataFrame] = [
            pd.read_csv(file)[['training_exp', 'training_items', 'training_timing']] for file in train_files
        ]
        self.eval_frames: list[pd.DataFrame] = [
            pd.read_csv(file)[['training_exp', 'eval_accuracy', 'eval_forgetting']] for file in eval_files
        ]
        self.experiences: list[int] = list(self.train_frames[0]['training_exp'].unique())
        self.n_experiences = len(self.experiences)

    def compute(self) -> tuple[str, list[int], pd.DataFrame]:
        # out_frame = pd.DataFrame(columns=self.COLUMNS)
        lines = []
        for exp in self.experiences:
            for i in range(len(self.train_frames)):
                train_frame = self.train_frames[i]
                eval_frame = self.eval_frames[i]
                train_frame = train_frame.loc[train_frame['training_exp'] == exp][['training_items', 'training_timing']]
                eval_frame = eval_frame.loc[eval_frame['training_exp'] == exp][['eval_accuracy', 'eval_forgetting']]

                train_means = train_frame.mean()
                eval_means = eval_frame.mean()

                line = [
                    exp,
                    train_means['training_items'],
                    train_means['training_timing'],
                    eval_means['eval_accuracy'],
                    eval_means['eval_forgetting'],
                ]

                lines.append(line)

                # line_frame = pd.DataFrame([line], columns=self.COLUMNS)
                # out_frame = pd.concat([out_frame, line_frame], sort=False)
        out_frame = pd.DataFrame(lines, columns=self.COLUMNS)
        return self.strategy_name, self.experiences, out_frame


class ExperimentPlotter:
    """
    Utility for plotting experiments graphs.
    """
    
    DEFAULT_EXECUTIONS = ['0', '1', '2']
    
    DEFAULT_STRATEGIES = [
        'naive',
        'cumulative',
        'joint_training',
        'replay_500',
        'replay_2500',
        'lwf',
    ]
    
    DEFAULT_OUT_FOLDER_RELPATH = 'graphs'
    
    def __init__(
            self,
            experiment_name: str,
            experiment_base_dir: str,
            executions: list[str] = None,
            strategies: list[str] = None,
            out_folder_root: str = None,
            out_folder_relpath: str = None,
            save_graphs: bool = False,
    ):
        self.experiment_name = experiment_name
        self.experiment_base_dir = os.path.join('..', experiment_base_dir)
        self.executions = self.DEFAULT_EXECUTIONS if executions is None else executions
        self.strategies = self.DEFAULT_STRATEGIES if strategies is None else strategies
        self.out_folder_root = self.experiment_base_dir if out_folder_root is None else out_folder_root
        self.out_folder_relpath = self.DEFAULT_OUT_FOLDER_RELPATH if out_folder_relpath is None else out_folder_relpath
        self.save_graphs = save_graphs

    def set_params(
            self,
            experiment_name: str,
            experiment_base_dir: str,
            executions: list[str] = None,
            strategies: list[str] = None,
            out_folder_root: str = None,
            out_folder_relpath: str = None,
            save_graphs: bool = False,
    ):
        self.experiment_name = experiment_name
        self.experiment_base_dir = os.path.join('..', experiment_base_dir)
        self.executions = self.DEFAULT_EXECUTIONS if executions is None else executions
        self.strategies = self.DEFAULT_STRATEGIES if strategies is None else strategies
        self.out_folder_root = self.experiment_base_dir if out_folder_root is None else out_folder_root
        self.out_folder_relpath = self.DEFAULT_OUT_FOLDER_RELPATH if out_folder_relpath is None else out_folder_relpath
        self.save_graphs = save_graphs

    # noinspection PyShadowingNames
    def create(self) -> tuple[list[int], dict[str, pd.DataFrame]]:
        frames: dict[str, pd.DataFrame] = {}
        experiences = None
        for strategy in self.strategies:
            train_csv_name = 'train_results.csv' if strategy != 'joint_training' else 'train_results_ext.csv'
            eval_csv_name = 'eval_results.csv' if strategy != 'joint_training' else 'eval_results_ext.csv'
            dir_paths = [
                os.path.join(self.experiment_base_dir, exec_id, strategy, 'csv') for exec_id in self.executions
            ]
            train_file_paths = [os.path.join(dir_path, train_csv_name) for dir_path in dir_paths]
            eval_file_paths = [os.path.join(dir_path, eval_csv_name) for dir_path in dir_paths]

            print('Train paths:')
            print(*train_file_paths, sep=',\n')
            print('Eval paths:')
            print(*eval_file_paths, sep=',\n')

            a = AClass(strategy, train_file_paths, eval_file_paths)
            strategy, experiences, frame = a.compute()
            print(strategy)
            print(frame)
            frames[strategy] = frame
        return experiences, frames

    @staticmethod
    def means_stdev(source_csv_path: str, dest_csv_path: str, columns: list[str]):
        src_frame = pd.read_csv(source_csv_path)[columns]
        means_lines = []
        stdev_lines = []
        experiences = list(src_frame[['Experience']].unique())
        for exp in experiences:
            sub_frame = src_frame.loc[src_frame['Experience'] == exp]
            means = sub_frame.mean()
            stdevs = sub_frame.std()

            line = [means[header] for header in columns]
            means_lines.append(line)

            line = [stdevs[header] for header in columns]
            stdev_lines.append(line)
        means_frame = pd.DataFrame(means_lines, columns=columns)
        stdev_frame = pd.DataFrame(stdev_lines, columns=columns)
        means_frame.to_csv(f"{dest_csv_path}_means.csv")
        stdev_frame.to_csv(f"{dest_csv_path}_stdevs.csv")

    def plot_graph(
            self, experiences: list[int], frames: dict[str, pd.DataFrame],
            out_file_name: str, header_name: str, x_label: str, y_label: str,
    ):
        """
        Naive -> { Experience, TrainingPatterns, TrainingTiming, ...}
        Cumulative -> { Experience, TrainingPatterns, TrainingTiming, ...}
        :param experiences: 
        :param frames: 
        :param out_file_name: 
        :param header_name: 
        :param x_label: 
        :param y_label:
        :return:
        """
        strategies = frames.keys()
        main_frame = None
        for strategy in strategies:
            frame = frames[strategy]
            if main_frame is None:
                main_frame = frame[['Experience']]
            local_frame = frame[[header_name]].rename(columns={header_name: strategy})
            main_frame = pd.concat([main_frame, local_frame], axis=1)
        print(main_frame)
        save_dir = os.path.join(self.out_folder_root, self.out_folder_relpath)
        os.makedirs(save_dir, exist_ok=True)
        main_frame.to_csv(os.path.join(save_dir, f"{self.experiment_name}_{out_file_name}.csv"))

        means_lines = []
        stdev_lines = []
        plt.figure()
        for exp in experiences:
            exp_frame = main_frame.loc[main_frame['Experience'] == exp]
            means = exp_frame.mean()
            stdevs = exp_frame.std()

            line = [exp] + [means[strategy] for strategy in strategies]
            means_lines.append(line)

            line = [exp] + [stdevs[strategy] for strategy in strategies]
            stdev_lines.append(line)

        means_frame = pd.DataFrame(means_lines, columns=['Experience']+list(strategies))
        stdevs_frame = pd.DataFrame(stdev_lines, columns=['Experience']+list(strategies))

        means_stdev_lines = []
        for i in range(len(means_lines)):
            means = means_lines[i]
            stdevs = stdev_lines[i]
            means_stdev_line = [means[0]]
            for j in range(1, len(means)):
                means_stdev_line += [means[j], stdevs[j]]
            means_stdev_lines.append(means_stdev_line)

        means_stdev_columns = ['Experience']
        for strategy in strategies:
            means_stdev_columns.append(f"{strategy}_means")
            means_stdev_columns.append(f"{strategy}_stdevs")
        means_stdevs_frame = pd.DataFrame(means_stdev_lines, columns=means_stdev_columns)
        means_stdevs_frame.to_csv(os.path.join(save_dir, f"{self.experiment_name}_{out_file_name}_means_stdev.csv"))

        y1 = means_frame.sub(stdevs_frame)
        y2 = means_frame.add(stdevs_frame)

        for strategy in strategies:
            plt.plot('Experience', strategy, data=means_frame)
            plt.fill_between(means_frame['Experience'], y1[strategy], y2[strategy], alpha=.25)

        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.legend()
        if self.save_graphs:
            plt.savefig(os.path.join(save_dir, f"{self.experiment_name}_{out_file_name}.png"))
        plt.show()

    # noinspection PyShadowingNames
    def timing_graph(self, experiences: list[int], frames: dict[str, pd.DataFrame]):
        self.plot_graph(
            experiences, frames, out_file_name='timing',
            header_name='TrainingTiming', x_label='experiences', y_label='time',
        )

    def patterns_graph(self, experiences: list[int], frames: dict[str, pd.DataFrame]):
        self.plot_graph(
            experiences, frames, out_file_name='patterns',
            header_name='TrainingItems', x_label='experiences', y_label='patterns',
        )
    
    def accuracy_graph(self, experiences: list[int], frames: dict[str, pd.DataFrame]):
        self.plot_graph(
            experiences, frames, out_file_name='accuracy',
            header_name='EvalAccuracy', x_label='experiences', y_label='accuracy',
        )
    
    def forgetting_graph(self, experiences: list[int], frames: dict[str, pd.DataFrame]):
        self.plot_graph(
            experiences, frames, out_file_name='forgetting',
            header_name='EvalForgetting', x_label='experiences', y_label='forgetting',
        )


if __name__ == '__main__':
    data = {
        'SplitMNIST': {
            'experiment_name': 'SplitMNIST',
            'experiment_base_dir': 'split_mnist_8_epochs',
        },
        'SplitCIFAR100': {
            'experiment_name': 'SplitCIFAR100',
            'experiment_base_dir': 'split_cifar100_8_epochs',
            'save_graphs': True,
        },
        'PermutedMNIST': {
            'experiment_name': 'PermutedMNIST',
            'experiment_base_dir': 'permuted_mnist_4_epochs',
        },
        'FileBasedSplitMNIST': {
            'experiment_name': 'FileBasedSplitMNIST',
            'experiment_base_dir': 'file_based_split_mnist_8_epochs',
        },
        'SplitTinyImageNet': {
            'experiment_name': 'SplitTinyImageNet',
            'experiment_base_dir': 'split_tiny_imagenet_multihead_mlp_10_epochs',
            'strategies': ['naive', 'cumulative', 'replay_500', 'replay_2500', 'lwf'],
            'save_graphs': True,
        },
    }

    plotter = ExperimentPlotter('', '')
    for exp_label, exp_data in data.items():
        plotter.set_params(**exp_data)
        experiences, frames = plotter.create()
        plotter.timing_graph(experiences, frames)
        plotter.patterns_graph(experiences, frames)
        plotter.accuracy_graph(experiences, frames)