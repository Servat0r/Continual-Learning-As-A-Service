from __future__ import annotations
from torchvision.transforms import ToTensor

from application.utils import TBoolStr, t, TDesc
from application.database import db
from application.data_managing import BaseDataManager
from application.resources import ResourceContext, DataType

from application.mongo.datasets import TDMDatasetDesc, greyscale_image_loader, \
    default_image_loader, data_manager_datasets_benchmark
from application.mongo.resources.mongo_base_configs import MongoEmbeddedBuildConfig, MongoBuildConfig

from .transform_builds import *
from .base_builds import *


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
        ok = all(name in ('root', 'all', 'files') for name in data.keys())
        if not ok:
            return False, "At least one unknown field."

        root = data.get('root', None)
        all_files = data.get('all', True)
        files = data.get('files', None)

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
        result = super(DataStreamFolderConfig, cls).create(data, context, save)
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
        return super(DataStreamExperienceConfig, cls).get_required()

    @classmethod
    def get_optionals(cls) -> set[str]:
        return super(DataStreamExperienceConfig, cls).get_optionals().union({'configs'})

    @classmethod
    def validate_input(cls, data: TDesc | list, context: ResourceContext) -> TBoolStr:
        if isinstance(data, list):
            data = {'configs': data}
        params: TDesc = {}
        extras = data.copy()

        for name in cls.get_required():
            val = data.get(name)
            if (val is not None) or cls.is_nullable(name):
                params[name] = val
                extras.pop(name)
            else:
                return False, f"None value was given for non-nullable field '{name}'."

        for name in cls.get_optionals():
            val = data.get(name)
            if (val is not None) or cls.is_nullable(name):
                params[name] = val
                extras.pop(name)
            else:
                return False, f"None value was given for non-nullable field '{name}'."
        # result: required & optional; data_copy: extras
        if len(extras) > 0 and not cls.has_extras():
            return False, "Unexpected extra arguments."

        configs = params.get('configs', [])
        if not isinstance(configs, list):
            raise TypeError("'configs' must be a list!")

        for i in range(len(configs)):
            result, msg = DataStreamFolderConfig.validate_input(configs[i], context)
            if not result:
                return False, f"Failed to build {i + 1}-th config: '{msg}'."

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
    train_transform = db.EmbeddedDocumentField(TransformConfig, default=None)
    train_target_transform = db.EmbeddedDocumentField(TransformConfig, default=None)
    eval_transform = db.EmbeddedDocumentField(TransformConfig, default=None)
    eval_target_transform = db.EmbeddedDocumentField(TransformConfig, default=None)
    other_transform_groups = db.MapField(
        db.ListField(db.EmbeddedDocumentField(TransformConfig)),
        default=None
    )

    # train_transform = db.StringField(choices=(None, TO_TENSOR), default=TO_TENSOR)
    # train_target_transform = db.StringField(choices=(None, TO_TENSOR), default=None)
    # eval_transform = db.StringField(choices=(None, TO_TENSOR), default=TO_TENSOR)
    # eval_target_transform = db.StringField(choices=(None, TO_TENSOR), default=None)

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
            'data_repository', 'complete_test_set_only',
            'other_streams', 'img_type', 'train_transform',
            'train_target_transform', 'eval_transform',
            'eval_target_transform', 'other_transform_groups',
        })

    @classmethod
    def _validate_stream_list(cls, stream_list: list[list[dict]], context: ResourceContext) -> TBoolStr:
        for i in range(len(stream_list)):
            result, msg = DataStreamExperienceConfig.validate_input(stream_list[i], context)
            if not result:
                return False, f"Failed to build {i + 1}-th stream: '{msg}'."
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

    @staticmethod
    def _validate_transform_data(transform_data: TDesc, context: ResourceContext) -> TBoolStr:
        if transform_data is not None:
            transform_config: t.Type[TransformConfig] = TransformConfig.get_by_name(transform_data)
            if transform_config is None:
                return False, "Not given or unknown transform."
            result, msg = transform_config.validate_input(transform_data, context)
            return result, None if result else f"Invalid transform: '{msg}'."
        else:
            return True, None

    @classmethod
    def validate_input(cls, data: TDesc, dtype: t.Type[DataType], context: ResourceContext) -> TBoolStr:
        result, msg = super(DataManagerBuildConfig, cls).validate_input(data, dtype, context)
        if not result:
            return result, msg
        iname, values = context.pop()
        params = values['params']

        train_stream_list = params['train_stream']  # list[list[dict]]
        test_stream_list = params['test_stream']  # list[list[dict]]
        other_streams_dict = params.get('other_streams', {})  # dict[str, # list[list[dict]]]

        img_type = params.get('img_type', DataManagerBuildConfig.RGB)  # string
        complete_test_set_only = params.get('complete_test_set_only', False)  # boolean

        """
        train_transform = params.get('train_transform', DataManagerBuildConfig.TO_TENSOR)   # string
        train_target_transform = params.get('train_target_transform', None)                 # string

        eval_transform = params.get('eval_transform', DataManagerBuildConfig.TO_TENSOR)     # string
        eval_target_transform = params.get('eval_target_transform', None)                   # string
        """

        train_transform_data = params.get('train_transform', None)
        train_target_transform_data = params.get('train_target_transform', None)

        eval_transform_data = params.get('eval_transform', None)
        eval_target_transform_data = params.get('eval_target_transform', None)

        for transform_data in (
                train_transform_data,
                train_target_transform_data,
                eval_transform_data,
                eval_target_transform_data,
        ):
            result, msg = cls._validate_transform_data(transform_data, context)
            if not result:
                return False, msg

        if not isinstance(img_type, str):
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

        other_transform_groups_data = params.get('other_transform_groups')
        if other_transform_groups_data is not None:
            check_other_transforms = isinstance(other_transform_groups_data, dict)

            if check_other_transforms:
                for stream_name, transforms in other_transform_groups_data.items():
                    if not isinstance(stream_name, str):
                        return False, "Names of the other transform groups must be strings!"
                    elif not isinstance(transforms, dict):
                        return False, "Other transform groups must be a dictionary of couples" \
                                      " (item_transform, target_transform)!"
                    else:
                        check_names = all(name in ('item', 'target') for name in transforms.keys())
                        if not check_names:
                            return False, "Other transform groups name indicators must be either 'item' or 'train'."
                        for transform_name, transform_data in transforms.items():
                            result, msg = cls._validate_transform_data(transform_data, context)
                            if not result:
                                return False, msg
                return True, None
            else:
                return False, "Parameter 'other_transform_groups' is not of the correct type!"
        return True, None

    @classmethod
    def create(cls, data: TDesc, tp: t.Type[DataType], context: ResourceContext, save: bool = True):
        ok, bc_name, params, extras = cls._filter_data(data)

        # streams processing
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

        # transforms processing
        for transform_name in (
                'train_transform',
                'train_target_transform',
                'eval_transform',
                'eval_target_transform',
        ):
            transform_data = params.get(transform_name)
            if transform_data is not None:
                transform_config: t.Type[TransformConfig] = TransformConfig.get_by_name(transform_data)
                if transform_config is None:
                    raise RuntimeError("Unknown or not given transform!")
                else:
                    params[transform_name] = transform_config.create(transform_data, context, save=False)

        # default train and eval transforms
        for transform_name in (
                'train_transform',
                'eval_transform',
        ):
            if params.get(transform_name) is None:
                params[transform_name] = ToTensorConfig.create({}, context, save=False)

        # other transform groups processing
        other_transform_groups_data: dict[str, dict[str, dict]] = params.get('other_transform_groups')
        if other_transform_groups_data is not None:
            other_transform_groups: dict[str, tuple[t.Any, t.Any]] = {}
            for stream_name, transform_group_data in other_transform_groups_data.items():
                item_transform_data = transform_group_data.get('item')
                item_transform = None
                if item_transform_data is not None:
                    item_transform_config: t.Type[TransformConfig] = TransformConfig.get_by_name(item_transform_data)
                    if item_transform_config is None:
                        raise RuntimeError("Not given or unknown item transform config")
                    item_transform = item_transform_config.create(item_transform_data, context, save)
                
                target_transform_data = transform_group_data.get('target')
                target_transform = None
                if target_transform_data is not None:
                    target_transform_config: t.Type[TransformConfig] = TransformConfig.get_by_name(target_transform_data)
                    if target_transform_config is None:
                        raise RuntimeError("Not given or unknown target transform config")
                    target_transform = target_transform_config.create(target_transform_data, context, save)

                other_transform_groups[stream_name] = (item_transform, target_transform)

            params['other_transform_groups'] = other_transform_groups

        # noinspection PyArgumentList
        benchmark_config = cls(**params)
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

            if self.train_transform is None:
                train_transform = None
            else:
                train_transform = self.train_transform.get_transform()

            if self.train_target_transform is None:
                train_target_transform = None
            else:
                train_target_transform = self.train_target_transform.get_transform()

            if self.eval_transform is None:
                eval_transform = None
            else:
                eval_transform = self.eval_transform.get_transform()

            if self.eval_target_transform is None:
                eval_target_transform = None
            else:
                eval_target_transform = self.eval_target_transform.get_transform()

            if self.other_transform_groups is None:
                other_transform_groups = None
            else:
                other_transform_groups = {}
                for stream_name, transform_configs in self.other_transform_groups.items():
                    item_transform_config = transform_configs[0]
                    item_transform = item_transform_config.get_transform()

                    target_transform_config = transform_configs[1]
                    target_transform = target_transform_config.get_transform()

                    other_transform_groups[stream_name] = (item_transform, target_transform)

            """
            train_transform = self.get_transform(self.train_transform)
            train_target_transform = self.get_transform(self.train_target_transform)

            eval_transform = self.get_transform(self.eval_transform)
            eval_target_transform = self.get_transform(self.eval_target_transform)
            """

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
                other_transform_groups=other_transform_groups,
            )
            # noinspection PyArgumentList
            return self.target_type()(benchmark)
        except Exception as ex:
            print(ex)
            return None
