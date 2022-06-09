from __future__ import annotations
import torch.utils.data as data

from avalanche.benchmarks import GenericCLScenario, dataset_benchmark
from avalanche.benchmarks.utils import AvalancheDataset, AvalancheDatasetType

from application.utils import t
from application.data_managing import BaseDataManager, BaseDataRepository


TFileAndLabel = t.TypeVar(
    'TFileAndLabel',
    bound=tuple[str, list[str], int],
)

TFileAndLabelAndBBox = t.TypeVar(
    'TFileAndLabelAndBBox',
    bound=tuple[str, list[str], int, t.Optional[t.Any]],
)

TFL = t.TypeVar(
    'TFL',
    bound=t.Union[TFileAndLabel, TFileAndLabelAndBBox],
)

TDMDatasetDesc = t.TypeVar(     # root, all, files
    'TDMDatasetDesc',
    bound=tuple[t.Optional[str], bool, t.Optional[list[str]]],
)

TDMDatasetLabel = t.TypeVar(    # label, all, files
    'TDMDatasetLabel',
    bound=dict[
        int,
        tuple[bool, t.Optional[list[str]]]
    ],
)

TDMDatasetConfig = t.TypeVar(
    'TDMDatasetConfig',
    bound=tuple[TDMDatasetDesc, TDMDatasetLabel, int],  # default label
)


def default_image_loader(manager: BaseDataManager, impath: str):
    return manager.default_image_loader(impath)


def greyscale_image_loader(manager: BaseDataManager, impath: str):
    return manager.greyscale_image_loader(impath)


class DataManagerDataset(data.Dataset):
    """
    This class extends the basic Pytorch Dataset class to handle list of paths
    as the main data source.
    """

    def __init__(
        self,
        manager: BaseDataManager,
        data_repository: BaseDataRepository,  # data repository in which files are contained
        config: list[TDMDatasetConfig],
        # (root (relative to base data repository folder), pick all files?, <file_path> for each file)
        loader: t.Callable = default_image_loader,  # image loader (default for the RGB one)
        transform=None,
        target_transform=None,
    ):
        if data_repository is None:
            raise ValueError("Data repository cannot be None!")
        self.manager = manager
        self.data_repository = data_repository
        self.files: list[str] = []
        self.targets: list[int] = []

        for desc, lbs, dfl_lb in config:
            dfl_lb = int(dfl_lb)
            print(desc, lbs, dfl_lb, sep=' *** ')  # todo togliere!
            root = desc[0]
            all_files = desc[1]
            files = desc[2]
            # for root, all_files, files in desc:
            current_files_and_labels: dict[str, int] = {}
            if all_files:
                files, targets = self.data_repository.get_all_files(root, include_labels=True)   # already normalized!
                # self.files += files
                # self.targets += targets
                for file in files:
                    current_files_and_labels[file] = dfl_lb
            else:
                for i in range(len(files)):
                    f = files[i]
                    fvals = f.split('/')
                    fvals = [val for val in fvals if len(val) > 0]
                    f = '/'.join(fvals)
                    if len(f) < 1:
                        raise RuntimeError("Invalid file path")
                    else:
                        files[i] = '/'.join([root, f])

                # self.files += files  # already normalized!
                # self.targets += [data_repository.get_file_label(fpath) for fpath in self.files]
                for file in files:
                    current_files_and_labels[file] = 0

            for label_val, label_files in lbs.items():
                label_val = int(label_val)
                all_files = label_files[0]
                if all_files:
                    for file in current_files_and_labels:
                        current_files_and_labels[file] = label_val
                else:
                    actual_files = label_files[1]
                    if actual_files is not None:
                        for file in actual_files:
                            current_files_and_labels[file] = label_val

            for file, label in current_files_and_labels.items():
                self.files.append(file)
                self.targets.append(label)

        self.loader = loader
        self.transform = transform
        self.target_transform = target_transform

    def __getitem__(self, index: int):
        """
        Returns next element in the dataset given the current index.

        :param index: index of the data to get.
        :return: loaded item.
        """
        img_path: str = self.files[index]
        img_abs_path: str = self.data_repository.get_absolute_path() + '/' + img_path
        img = self.loader(self.manager, img_abs_path)
        target = self.targets[index]

        if self.transform is not None:
            img = self.transform(img)
        if self.target_transform is not None:
            target = self.target_transform(target)

        return img, target

    def __len__(self):
        """
        Returns the total number of elements in the dataset.

        :return: Total number of dataset items.
        """

        return len(self.files)

    def __repr__(self):
        return f"{type(self).__name__} [manager = {self.manager}, repository = {self.data_repository}]"

    def __str__(self):
        return self.__repr__()


def data_manager_dataset_stream(
        stream_name: str,
        manager: BaseDataManager,
        data_repository: BaseDataRepository,
        files: list[list[TDMDatasetConfig]],
        loader: t.Callable = default_image_loader,
        transform=None,
        target_transform=None,
        transform_groups: dict = None,
        task_labels: int | list[int] = None,
) -> list[DataManagerDataset | AvalancheDataset]:
    """
    Helper function to
    :param stream_name:
    :param manager:
    :param data_repository:
    :param files:
    :param loader:
    :param transform:
    :param target_transform:
    :param transform_groups:
    :param task_labels:
    :return:
    """
    n_experiences = len(files)
    if task_labels is not None and isinstance(task_labels, int):
        task_labels_list = []
        for i in range(n_experiences):
            task_labels_list.append(task_labels)
        task_labels = task_labels_list
    elif isinstance(task_labels, list):
        if len(task_labels) != n_experiences:
            raise ValueError("Task labels length must match files length!")

    # now task_labels is either None or a list of int

    if transform_groups is None:
        transform_groups = {}
    transform_groups[stream_name] = (transform, target_transform)

    datasets: list[AvalancheDataset] = []
    for i in range(n_experiences):
        desc = files[i]
        dset = DataManagerDataset(manager, data_repository, desc, loader)
        datasets.append(
            AvalancheDataset(
                dset, task_labels=(task_labels[i] if task_labels is not None else None),
                dataset_type=AvalancheDatasetType.CLASSIFICATION,
            )
        )
    return datasets


def data_manager_datasets_benchmark(
        manager: BaseDataManager,
        data_repository: BaseDataRepository,

        train_build_data: list[list[TDMDatasetConfig]],
        eval_build_data: list[list[TDMDatasetConfig]],

        other_build_data: dict[str, list[list[TDMDatasetDesc]]] = None,
        complete_test_set_only: bool = False,
        loader: t.Callable = default_image_loader,

        task_labels: int | list[int] = None,

        train_transform=None, train_target_transform=None,
        eval_transform=None, eval_target_transform=None,
        other_transform_groups: dict[str, t.Sequence[t.Any, t.Any]] = None,

) -> GenericCLScenario:

    train_datasets = data_manager_dataset_stream(
        'train', manager, data_repository,
        train_build_data, loader=loader,
        task_labels=task_labels,
    )
    test_datasets = data_manager_dataset_stream(
        'eval', manager, data_repository,
        eval_build_data, loader=loader,
        task_labels=task_labels,
    )
    other_stream_datasets: dict[str, list[DataManagerDataset]] | None = {}

    if other_build_data is None or len(other_build_data) == 0:
        other_stream_datasets = None
    else:
        for stream_name, stream_build in other_build_data.items():
            other_stream_datasets[stream_name] = data_manager_dataset_stream(
                stream_name, manager, data_repository,
                stream_build, loader=loader,
                task_labels=task_labels,
            )

    if other_transform_groups is not None:
        for stream_name, transforms in other_transform_groups.items():
            other_transform_groups[stream_name] = tuple(transforms)

    return dataset_benchmark(
        train_datasets, test_datasets, other_streams_datasets=other_stream_datasets,
        complete_test_set_only=complete_test_set_only, train_transform=train_transform,
        train_target_transform=train_target_transform, eval_transform=eval_transform,
        eval_target_transform=eval_target_transform, other_streams_transforms=other_transform_groups,
     )


__all__ = [
    'TDMDatasetDesc',
    'TDMDatasetLabel',
    'TDMDatasetConfig',

    'default_image_loader',
    'greyscale_image_loader',
    'DataManagerDataset',
    'data_manager_dataset_stream',
    'data_manager_datasets_benchmark',
]