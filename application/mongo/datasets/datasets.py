from __future__ import annotations
import torch.utils.data as data

from avalanche.benchmarks.utils import AvalancheDataset
from avalanche.benchmarks import GenericCLScenario, dataset_benchmark

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

TDMDatasetDesc = t.TypeVar(
    'TDMDatasetDesc',
    bound=tuple[t.Optional[str], bool, t.Optional[list[str]]],
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

    def __init__(self,
                 manager: BaseDataManager,
                 data_repository: BaseDataRepository,  # data repository in which files are contained
                 desc: list[TDMDatasetDesc],
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

        for root, all_files, files in desc:
            if all_files:
                files, targets = self.data_repository.get_all_files(root, include_labels=True)   # already normalized!
                self.files += files
                self.targets += targets
            else:
                for i in range(len(files)):
                    # todo refactor to method for eliminating '/' at start and end!
                    f = files[i]
                    if len(f) < 1:
                        raise RuntimeError("Invalid file path")
                    elif f[0] == '/':
                        f = f[1:]
                        if len(f) < 1:
                            raise RuntimeError("Invalid file path")
                        elif f[-1] == '/':
                            f = f[:-1]
                            if len(f) < 1:
                                raise RuntimeError("Invalid file path")
                    files[i] = root + '/' + f

                self.files += files  # already normalized!
                self.targets += [data_repository.get_file_label(fpath) for fpath in self.files]

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


def data_manager_dataset_stream(
        stream_name: str,
        manager: BaseDataManager,
        data_repository: BaseDataRepository,
        files: list[list[TDMDatasetDesc]],
        loader: t.Callable = default_image_loader,
        transform=None,
        target_transform=None,
        transform_groups: dict = None,
) -> list[AvalancheDataset]:  # todo anche altro?
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
    :return:
    """
    if transform_groups is None:
        transform_groups = {}
    transform_groups[stream_name] = (transform, target_transform)

    datasets: list[AvalancheDataset] = []
    for i in range(len(files)):
        desc = files[i]
        dset = DataManagerDataset(manager, data_repository, desc, loader)
        datasets.append(AvalancheDataset(
            dset, transform_groups=transform_groups, initial_transform_group=stream_name,
        ))
    return datasets


def data_manager_datasets_benchmark(
        manager: BaseDataManager,
        data_repository: BaseDataRepository,

        train_build_data: list[list[TDMDatasetDesc]],
        eval_build_data: list[list[TDMDatasetDesc]],

        other_build_data: dict[str, list[list[TDMDatasetDesc]]] = None,
        complete_test_set_only: bool = False,
        loader: t.Callable = default_image_loader,

        train_transform=None, train_target_transform=None,
        eval_transform=None, eval_target_transform=None,
        other_transform_groups: dict[str, tuple[t.Any, t.Any]] = None,

) -> GenericCLScenario:
    train_datasets = data_manager_dataset_stream('train', manager, data_repository, train_build_data, loader)
    test_datasets = data_manager_dataset_stream('eval', manager, data_repository, eval_build_data, loader)
    other_stream_datasets: dict[str, list[AvalancheDataset]] | None = {}
    if other_build_data is None or len(other_build_data) == 0:
        other_stream_datasets = None
    else:
        for stream_name, stream_build in other_build_data.items():
            other_stream_datasets[stream_name] = data_manager_dataset_stream(
                stream_name, manager, data_repository, stream_build, loader,
            )
    return dataset_benchmark(
        train_datasets, test_datasets, other_streams_datasets=other_stream_datasets,
        complete_test_set_only=complete_test_set_only, train_transform=train_transform,
        train_target_transform=train_target_transform, eval_transform=eval_transform,
        eval_target_transform=eval_target_transform, other_streams_transforms=other_transform_groups,
     )


__all__ = [
    'TDMDatasetDesc',
    'default_image_loader',
    'greyscale_image_loader',
    'DataManagerDataset',
    'data_manager_dataset_stream',
    'data_manager_datasets_benchmark',
]