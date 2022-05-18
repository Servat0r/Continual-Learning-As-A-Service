from __future__ import annotations
from torchvision.transforms import ToTensor
from avalanche.benchmarks.classic import SplitMNIST

from application.utils import TBoolStr, t, TDesc
from application.database import db
from application.data_managing import BaseDataManager

from application.resources.contexts import ResourceContext
from application.resources.base import DataType

from application.mongo.resources.mongo_base_configs import *
from application.mongo.datasets import TDMDatasetDesc, data_manager_datasets_benchmark, \
    greyscale_image_loader, default_image_loader
from .base_builds import *


# SplitMNIST builder
@MongoBuildConfig.register_build_config('SplitMNIST')
class SplitMNISTBuildConfig(MongoBaseBenchmarkBuildConfig):
    """
    Build config for a standard SplitMNIST benchmark based on avalanche.benchmarks.classics#SplitMNIST function.
    """
    n_experiences = db.IntField(required=True)
    return_task_id = db.BooleanField(required=False, default=False)
    seed = db.IntField(default=None)
    fixed_class_order = db.ListField(db.IntField(), default=None)
    shuffle = db.BooleanField(default=True)
    dataset_root = db.StringField(default=None)

    @classmethod
    def get_required(cls) -> set[str]:
        return super().get_required().union({'n_experiences'})

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super().get_optionals().union({
            'return_task_id',
            'seed',
            'fixed_class_order',
            'shuffle',
            'dataset_root',
        })

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type('Benchmark')

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        result, msg = super().validate_input(data, dtype, context)
        if not result:
            return result, msg
        iname, values = context.pop()
        params = values['params']
        result = all(isinstance(val, int) for val in params.values())
        return result, None if result else "One or more parameter(s) is/are incorrect."

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: ResourceContext, save: bool = True):
        return super().create(data, tp, context, save)

    def build(self, context: ResourceContext, locked=False, parents_locked=False):
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


# FashionMNIST builder


# PathsDataset builder and helper
class DataStreamFolderConfig(MongoEmbeddedBuildConfig):

    """
    Representing a single folder config, i.e. of the form:
    {
        "root": ...,
        "all": ...,
        "files": [
            ...
        ]
    }
    """
    root = db.StringField(default=None)
    all = db.BooleanField(default=True)
    files = db.ListField(db.StringField(), default=None)

    @classmethod
    def get_required(cls) -> set[str]:
        return super(DataStreamFolderConfig, cls).get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(DataStreamFolderConfig, cls).get_optionals().union({'root', 'all', 'files'})

    @classmethod
    def validate_input(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        result, msg = super(DataStreamFolderConfig, cls).validate_input(data, context)
        if not result:
            return result, msg
        
        iname, values = context.pop()
        params = values['params']
        
        root = params.get('root', None)
        all_files = params.get('all', True)
        files = params.get('files', None)
        
        if root is not None and not isinstance(root, str):
            return False, "'root' parameter must be a string!"
        
        if not isinstance(all_files, bool):
            return False, "'all' parameter must be a boolean!"
        
        if files is not None:
            if not isinstance(files, list):
                return False, "'files' parameter must be a list!"

            all_str = all(isinstance(item, str) for item in files)
            if not all_str:
                return False, "'files' parameter must contain only strings!"

        return True, None

    @classmethod
    def create(cls, data: TDesc, context: ResourceContext, save: bool = True) -> DataStreamFolderConfig | None:
        result = super().create(data, context, save)
        return None if result is None else t.cast(DataStreamFolderConfig, result)

    def get_root(self) -> str | None:
        return self.root

    def all_files(self) -> bool:
        return self.all

    def get_files(self) -> list[str] | None:
        return self.files

    def to_tuple(self) -> TDMDatasetDesc:
        return self.root, self.all, self.files


class DataStreamExperienceConfig(MongoEmbeddedBuildConfig):
    """
    Representing configuration for each experience, i.e. of the form:
    [
        {
            "root": ...,
            "all": ...,
            "files": [
            ...
            ]
        },
        {
            ...
        },
        ...
    ]
    """

    configs = db.ListField(db.EmbeddedDocumentField(DataStreamFolderConfig), default=[])

    @classmethod
    def get_required(cls) -> set[str]:
        return super().get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super().get_optionals().union({'configs'})

    @classmethod
    def validate_input(cls, data: TDesc | list, context: ResourceContext) -> TBoolStr:
        if isinstance(data, list):
            data = {'configs': data}
        result, msg = super(DataStreamExperienceConfig, cls).validate_input(data, context)
        if not result:
            return result, msg

        iname, values = context.pop()
        params = values['params']

        configs = params.get('configs', [])
        if not isinstance(configs, list):
            raise TypeError("'configs' must be a list!")

        for i in range(len(configs)):
            result, msg = DataStreamFolderConfig.validate_input(configs[i], context)
            if not result:
                return False, f"Failed to build {i+1}-th config: '{msg}'."

        return True, None

    @classmethod
    def create(cls, data: TDesc, context: ResourceContext, save: bool = True) -> DataStreamExperienceConfig | None:
        ok, bc_name, params, extras = cls._filter_data(data)
        configs = params.get('configs', [])
        objs: list[DataStreamFolderConfig] = []

        for i in range(len(configs)):
            dsf_config = DataStreamFolderConfig.create(configs[i], context, save=False)
            if dsf_config is None:
                return None
            else:
                objs.append(dsf_config)

        params['configs'] = []  # objs

        # noinspection PyArgumentList
        exp_config = cls(**params)
        exp_config.configs = objs
#        for i in range(len(objs)):
#            exp_config.configs.append(objs[i])
        return exp_config

    def get_document_configs(self) -> list[DataStreamFolderConfig]:
        return self.configs

    def get_tuple_configs(self) -> list[TDMDatasetDesc]:
        return [config.to_tuple() for config in self.configs]


@MongoBuildConfig.register_build_config('DataManagerBenchmark')
class DataManagerBuildConfig(MongoBaseBenchmarkBuildConfig):
    """
    This build config models a benchmark built starting from
    a set of data in a data repository, similarly to what
    happens for paths_benchmark.
    The configuration has the following syntax:
    {
        "name": "DataManagerBenchmark",
        "data_repository": <data_repository_name>,
        "img_type": "greyscale"/"RGB",       # image type (determines which image loader to use)
        "complete_test_set_only": true/false,
        "train_stream": [  # train stream
            # experience #1 #
            [
                {
                    "root": <root_path>,  # (within the data repository; if not given, it is intended as repo root)
                    "all": true/false, # if true, loads all files in the data repo; otherwise, loads the given ones;
                    "files": [         # list of file paths (relative to root) to load;
                        <path>,
                        <path>,
                        ...
                    ]
                },
                {
                    "root": ...,
                    "all": ...,
                    "files": [
                        ...
                    ]
                },
                ...
            ],
            # experience #2 #
            ...
        ],
        "test_stream": [  # test stream
            # experience #1 #
            [
                {
                    "root": <root_path>,
                    "all": true/false,
                    "files": [
                        ...
                    ]
                },
                {
                    "root": ...,
                    "all": ...,
                    "files": [
                        ...
                    ]
                },
                ...
            ],
            # experience #2 #
            ...
        ],
        "other_streams": {    # Other benchmark streams
            <stream_name>: [
                [
                    {
                        "root": ...,
                        "all": ...
                        "files": [
                        ...
                        ]
                    },
                    ...
                ],
                ...
            ],
            ...
        }
    }
    """

    # Image types
    L = 'greyscale'
    RGB = 'RGB'

    # Transform types
    TO_TENSOR = "ToTensor"

    # Fields
    # Streams
    train_stream = db.ListField(db.EmbeddedDocumentField(DataStreamExperienceConfig), required=True)
    test_stream = db.ListField(db.EmbeddedDocumentField(DataStreamExperienceConfig), required=True)
    other_streams = db.MapField(
        db.ListField(db.EmbeddedDocumentField(DataStreamExperienceConfig), default=[]),
        default={},
    )
    # Other parameters
    img_type = db.StringField(choices=(L, RGB), default=RGB)
    complete_test_set_only = db.BooleanField(default=False)

    # Transforms
    train_transform = db.StringField(choices=(None, TO_TENSOR), default=TO_TENSOR)
    train_target_transform = db.StringField(choices=(None, TO_TENSOR), default=None)
    eval_transform = db.StringField(choices=(None, TO_TENSOR), default=TO_TENSOR)
    eval_target_transform = db.StringField(choices=(None, TO_TENSOR), default=None)

    def get_loader(self):
        img_type = self.img_type

        if img_type == DataManagerBuildConfig.L:
            return greyscale_image_loader
        elif img_type == DataManagerBuildConfig.RGB:
            return default_image_loader
        else:
            raise ValueError("Unknown image type")

    @staticmethod
    def get_transform(transform_name: str):
        if transform_name == DataManagerBuildConfig.TO_TENSOR:
            return ToTensor()

    @classmethod
    def get_required(cls) -> set[str]:
        return super(DataManagerBuildConfig, cls).get_required().union({'train_stream', 'test_stream'})

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(DataManagerBuildConfig, cls).get_optionals().union({
            'data_repository',
            'complete_test_set_only',
            'other_streams', 'img_type',
            'train_transform', 'train_target_transform',
            'eval_transform', 'eval_target_transform',
        })

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type('Benchmark')

    @classmethod
    def _validate_stream_list(cls, stream_list: list[list[dict]], context: ResourceContext) -> TBoolStr:
        for i in range(len(stream_list)):
            result, msg = DataStreamExperienceConfig.validate_input(stream_list[i], context)
            if not result:
                return False, f"Failed to build {i+1}-th stream: '{msg}'."
        return True, None

    @classmethod
    def _create_stream_list(cls, stream_list: list[list[dict]],
                            context: ResourceContext) -> list[DataStreamExperienceConfig] | None:
        exp_configs: list[DataStreamExperienceConfig] = []
        for i in range(len(stream_list)):
            stream = DataStreamExperienceConfig.create({'configs': stream_list[i]}, context, save=False)
            if stream is None:
                return None
            else:
                exp_configs.append(stream)
        return exp_configs

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        result, msg = super(DataManagerBuildConfig, cls).validate_input(data, dtype, context)
        if not result:
            return result, msg
        iname, values = context.pop()
        params = values['params']
        
        train_stream_list = params['train_stream']                                      # list[list[dict]]
        test_stream_list = params['test_stream']                                        # list[list[dict]]
        other_streams_dict = params.get('other_streams', {})                            # dict[str, # list[list[dict]]]

        img_type = params.get('img_type', DataManagerBuildConfig.RGB)                       # string
        complete_test_set_only = params.get('complete_test_set_only', False)                # boolean

        train_transform = params.get('train_transform', DataManagerBuildConfig.TO_TENSOR)   # string
        train_target_transform = params.get('train_target_transform', None)                 # string

        eval_transform = params.get('eval_transform', DataManagerBuildConfig.TO_TENSOR)     # string
        eval_target_transform = params.get('eval_target_transform', None)                   # string

        # string fields
        all_str_none = all(par is None or isinstance(par, str)
                           for par in [train_target_transform, eval_target_transform])
        if not all_str_none:
            return False, "One or more parameters are not of the correct (str | None) type."

        all_str = all(isinstance(par, str) for par in [img_type, train_transform, eval_transform])
        if not all_str:
            return False, "One or more parameters are not of the correct (str) type."

        # boolean field(s)
        if not isinstance(complete_test_set_only, bool):
            return False, "'complete_test_set_only' must be a boolean."

        # list[list[dict]] / dict[str, list[list[dict]] ] fields
        for stream_list in [train_stream_list, test_stream_list]:
            result, msg = cls._validate_stream_list(stream_list, context)
            if not result:
                return False, msg

        for stream_name, stream_list in other_streams_dict.items():
            result, msg = cls._validate_stream_list(stream_list, context)
            if not result:
                return False, msg
            other_streams_dict[stream_name]: list[DataStreamExperienceConfig] = stream_list

        return True, None

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: ResourceContext, save: bool = True):
        ok, bc_name, params, extras = cls._filter_data(data)
        train_stream_list_config = params['train_stream']
        test_stream_list_config = params['test_stream']
        other_streams_dict_config = params.get('other_streams', {})

        train_stream_list = cls._create_stream_list(train_stream_list_config, context)
        test_stream_list = cls._create_stream_list(test_stream_list_config, context)

        other_streams_dict = {}
        for stream_name, stream_list_config in other_streams_dict_config.items():
            stream_list = cls._create_stream_list(stream_list_config, context)
            other_streams_dict[stream_name] = stream_list

        params['train_stream'] = train_stream_list
        params['test_stream'] = test_stream_list
        params['other_streams'] = other_streams_dict

        # noinspection PyArgumentList
        benchmark_config = cls(**params)

        #for tstream in train_stream_list:
        #    benchmark_config.train_stream.append(tstream)

        #for tstream in test_stream_list:
        #    benchmark_config.test_stream.append(tstream)

        #for stream_name, stream_value in other_streams_dict.items():
        #    benchmark_config.other_streams[stream_name] = stream_value

        return benchmark_config

    def build(self, context: ResourceContext, locked=False, parents_locked=False):
        try:
            train_build_data: list[list[TDMDatasetDesc]] = [config.get_tuple_configs() for config in self.train_stream]
            test_build_data: list[list[TDMDatasetDesc]] = [config.get_tuple_configs() for config in self.test_stream]

            other_build_data: dict[str, : list[list[TDMDatasetDesc]]] = \
                None if self.other_streams is None or len(self.other_streams) == 0 else {}

            if other_build_data is not None:
                for stream_name, stream_desc in self.other_streams.items():
                    other_build_data[stream_name] = [config.get_tuple_configs() for config in stream_desc]

            loader = self.get_loader()

            train_transform = self.get_transform(self.train_transform)
            train_target_transform = self.get_transform(self.train_target_transform)

            eval_transform = self.get_transform(self.eval_transform)
            eval_target_transform = self.get_transform(self.eval_target_transform)

            benchmark = data_manager_datasets_benchmark(
                BaseDataManager.get(),
                self.data_repository,
                train_build_data,
                test_build_data,
                other_build_data,
                self.complete_test_set_only,
                loader,
                train_transform,
                train_target_transform,
                eval_transform,
                eval_target_transform,
                other_transform_groups=None,  # todo implement in build config!
            )
            # noinspection PyArgumentList
            return self.target_type()(benchmark)
        except Exception as ex:
            print(ex)
            return None


__all__ = [
    'SplitMNISTBuildConfig',
    'DataManagerBuildConfig',
]
