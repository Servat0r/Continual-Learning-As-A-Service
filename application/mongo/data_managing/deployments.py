from __future__ import annotations

import torch

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


__all__ = [
    'ExperimentExportModelDeployer',
]