from __future__ import annotations

import torch
from torchvision.models import *

from application.utils import TDesc, TBoolStr, t
from application.models import User, Workspace
from application.data_managing import BaseModelDeployer, BaseDataManager

from application.resources.base import DataType, ReferrableDataType
from application.resources.contexts import UserWorkspaceResourceContext

from application.mongo.base import MongoBaseUser, MongoBaseWorkspace


@BaseModelDeployer.register_model_deployer('ExperimentExport')
class ExperimentExportModelDeployer(BaseModelDeployer):

    @classmethod
    def validate_input(cls, data: TDesc, context: UserWorkspaceResourceContext) -> TBoolStr:
        required = ['experiment', 'execution']
        check_required = all(field in data for field in required)
        if not check_required:
            return False, "Missing one or more required parameter."
        experiment = data.get('experiment')
        execution = data.get('execution')
        if not isinstance(experiment, str):
            return False, "'experiment' parameter must be a string!"
        if not isinstance(execution, int):
            return False, "'execution' parameter must be an integer!"
        return True, None

    @classmethod
    def deploy_model(cls, data: TDesc, context: UserWorkspaceResourceContext, name: str, path: str) -> TBoolStr:
        experiment_name = data.get('experiment')
        execution_id = data.get('execution')
        owner = t.cast(MongoBaseUser, User.canonicalize(context.get_username()))
        workspace = t.cast(MongoBaseWorkspace, Workspace.canonicalize(context))
        base_dir = workspace.models_base_dir_parents() + [workspace.models_base_dir()]
        path_dir = path.split('/')
        path_dir = [s for s in path_dir if len(s) > 0]
        path_dirs = base_dir + path_dir
        ExperimentClass = t.cast(ReferrableDataType, DataType.get_type('BaseCLExperiment')).config_type()
        experiment_config = ExperimentClass.get_one(owner, workspace, experiment_name)
        if experiment_config is None:
            return False, "Not existing experiment config"
        execution = experiment_config.get_execution(execution_id)
        if execution.completed:
            model_fd = execution.get_final_model(descriptor=True)
            model = torch.load(model_fd)
            manager = BaseDataManager.get()
            result, exc = manager.save_model(model, path_dirs, name + '.pt')
            return result, exc
        else:
            return False, "Experiment execution not completed"


@BaseModelDeployer.register_model_deployer('TorchvisionExport')
class TorchvisionExportModelDeployer(BaseModelDeployer):
    """
    Deployer syntax:
    {
        "name": "TorchvisionExport",
        "net_type": <net_name>,
        "pretrained": true/false
    }
    """

    # torchvision (supported) models
    __NETS__ = {
        'AlexNet': alexnet,
        'GoogleNet': googlenet,

        'ResNet18': resnet18,
        'ResNet34': resnet34,
        'ResNet50': resnet50,
        'ResNet101': resnet101,
        'ResNet152': resnet152,

        'SqueezeNet10': squeezenet1_0,
        'SqueezeNet11': squeezenet1_1,

        'DenseNet121': densenet121,
        'DenseNet161': densenet161,
        'DenseNet169': densenet169,
        'DenseNet201': densenet201,

        'MobileNet_v2': mobilenet_v2,
        'MobileNet_v3_small': mobilenet_v3_small,
        'MobileNet_v3_large': mobilenet_v3_large,

        'EfficientNet_b0': efficientnet_b0,
        'EfficientNet_b1': efficientnet_b1,
        'EfficientNet_b2': efficientnet_b2,
        'EfficientNet_b3': efficientnet_b3,
        'EfficientNet_b4': efficientnet_b4,
        'EfficientNet_b5': efficientnet_b5,
        'EfficientNet_b6': efficientnet_b6,
        'EfficientNet_b7': efficientnet_b7,

        'RegNet_y_400mf': regnet_y_400mf,
        'RegNet_y_800mf': regnet_y_800mf,
        'RegNet_y_1_6gf': regnet_y_1_6gf,
        'RegNet_y_3_2gf': regnet_y_3_2gf,
        'RegNet_y_8gf': regnet_y_8gf,
        'RegNet_y_16gf': regnet_y_16gf,
        'RegNet_y_32gf': regnet_y_32gf,
        'RegNet_y_128gf': regnet_y_128gf,
        'RegNet_x_400mf': regnet_x_400mf,
        'RegNet_x_800mf': regnet_x_800mf,
        'RegNet_x_1_6gf': regnet_x_1_6gf,
        'RegNet_x_3_2gf': regnet_x_3_2gf,
        'RegNet_x_8gf': regnet_x_8gf,
        'RegNet_x_16gf': regnet_x_16gf,
        'RegNet_x_32gf': regnet_x_32gf,

        'ConvNext_tiny': convnext_tiny,
        'ConvNext_small': convnext_small,
        'ConvNext_base': convnext_base,
        'ConvNext_large': convnext_large,
    }

    @classmethod
    def validate_input(cls, data: TDesc, context: UserWorkspaceResourceContext) -> TBoolStr:
        required = ['net_type', 'pretrained']
        req_check = all(req in data for req in required)
        if not req_check:
            return False, "One or more parameter(s) does not exist."
        net_type = data.get('net_type')
        pretrained = data.get('pretrained')
        typecheck = isinstance(net_type, str) and isinstance(pretrained, bool)
        if not typecheck:
            return False, "'net_type' parameter must be a string and 'pretrained' must be a boolean"
        validnet = net_type in cls.__NETS__
        return validnet, None if validnet else f"Unknown net_type '{net_type}'"

    @classmethod
    def deploy_model(cls, data: TDesc, context: UserWorkspaceResourceContext, name: str, path: str) -> TBoolStr:
        net_type = data.get('net_type')
        pretrained = data.get('pretrained')
        net_func = cls.__NETS__.get(net_type)
        if net_func is None:
            return False, f"Unknown net '{net_type}'"
        model = net_func(pretrained=pretrained)

        workspace = t.cast(MongoBaseWorkspace, Workspace.canonicalize(context))
        base_dir = workspace.models_base_dir_parents() + [workspace.models_base_dir()]
        path_dir = path.split('/')
        path_dir = [s for s in path_dir if len(s) > 0]
        path_dirs = base_dir + path_dir

        manager = BaseDataManager.get()
        result, exc = manager.save_model(model, path_dirs, name + '.pt')
        return result, exc


__all__ = [
    'ExperimentExportModelDeployer',
    'TorchvisionExportModelDeployer',
]