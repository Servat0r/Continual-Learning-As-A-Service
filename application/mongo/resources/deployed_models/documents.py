from __future__ import annotations

import torch
from datetime import datetime

from application.database import *
from application.utils import t, TBoolExc, TDesc, get_device, TBoolStr, auto_tboolexc
from application.data_managing import BaseDataManager, BaseModelDeployer
from application.models import User, Workspace

from application.resources.base import DataType, BaseMetadata
from application.resources.contexts import UserWorkspaceResourceContext

from application.mongo.base import MongoBaseUser, MongoBaseWorkspace
from application.mongo.mongo_base_metadata import MongoBaseMetadata
from application.mongo.resources.mongo_base_configs import *


class MongoDeployedModelMetadata(MongoBaseMetadata):
    pass


class MongoDeployedModelConfig(MongoBaseResourceConfig):

    path = db.StringField(default=None)

    def to_dict(self, links=True) -> TDesc:
        data = super().to_dict(links=links)
        data['path'] = self.get_path()
        return data

    @staticmethod
    def target_type() -> t.Type[DataType]:
        return DataType.get_type('DeployedModel')

    @staticmethod
    def meta_type() -> t.Type[BaseMetadata]:
        return MongoDeployedModelMetadata

    def get_owner(self):
        return self.owner

    def get_workspace(self):
        return self.workspace

    def get_name(self):
        return self.name

    def get_path(self):
        return self.path

    def get_path_list(self):
        result = self.path.split('/')
        result = [s for s in result if len(s) > 0]
        return result

    def get_metadata(self):
        return self.metadata.to_dict(links=False)

    def base_dir(self) -> list[str]:
        return self.workspace.models_base_dir_parents() + [self.workspace.models_base_dir()]

    # ok
    def get_model(self) -> torch.nn.Module:
        path_dirs = self.base_dir() + self.get_path_list()
        manager = BaseDataManager.get()
        model_fd = manager.get_file_pointer(self.name + '.pt', path_dirs)
        model = torch.load(model_fd).to(get_device())
        return model

    def set_model(self, model: torch.nn.Module) -> TBoolExc:
        path_dirs = self.base_dir() + self.get_path_list()
        manager = BaseDataManager.get()
        result, exc = manager.save_model(model, path_dirs, self.name + '.pt')
        return result, exc

    # ok
    @classmethod
    def validate_input(cls, data, context: UserWorkspaceResourceContext) -> TBoolStr:
        required = ['name', 'path', 'deploy']
        check_required = all(field in data for field in required)
        if not check_required:
            return False, "Missing parameter(s)."
        name = data.get('name')
        path = data.get('path')
        deploy_data = data.get('deploy')
        description = data.get('description', '')
        check_str = all(isinstance(f, str) for f in [name, path, description])
        if not check_str:
            return False, "'name' and 'description' must be string!"
        if not isinstance(deploy_data, dict):
            return False, "'deploy_data' must be a dictionary!"
        deployer = BaseModelDeployer.get_by_name(deploy_data)
        if deployer is None:
            return False, "Failed to validate deployment data: unknown or missing deployer name."
        result, msg = deployer.validate_input(deploy_data, context)
        return result, None if result else f"Failed to validate deployment data: '{msg}'."

    @classmethod
    def create(cls, data, context: UserWorkspaceResourceContext, save: bool = True,
               parents_locked=False, **metadata):
        result, msg = cls.validate_input(data, context)
        if not result:
            return result, msg
        name = data.get('name')
        path = data.get('path')
        description = data.get('description', '')
        owner = t.cast(MongoBaseUser, User.canonicalize(context.get_username()))
        workspace = t.cast(MongoBaseWorkspace, Workspace.canonicalize(context))
        now = datetime.utcnow()

        if metadata is None:
            metadata = {}
        metadata['created'] = now
        metadata['last_modified'] = now

        with workspace.sub_resource_create(parents_locked=parents_locked):
            deploy_data = data.get('deploy')
            deployer = BaseModelDeployer.get_by_name(deploy_data)
            if deployer is None:
                return None
            result, msg = deployer.deploy_model(deploy_data, context, name, path)
            if not result:
                return f"Failed to deploy model: '{msg}'"
            # noinspection PyArgumentList
            obj = cls(
                name=name,
                description=description,
                owner=owner,
                path=path,
                workspace=workspace,
                metadata=cls.meta_type()(**metadata),
            )
            if obj is not None:
                with obj.resource_create(parents_locked=True):
                    if save:
                        obj.save(create=True)
            return obj

    # ok
    def build(self, context: UserWorkspaceResourceContext,
              locked=False, parents_locked=False):
        with self.resource_read(locked=locked, parents_locked=parents_locked):
            model = self.get_model()
            # noinspection PyArgumentList
            obj = self.target_type()(model)
            # noinspection PyUnresolvedReferences
            obj.set_metadata(
                name=self.name,
                path=self.path,
                owner=self.owner.username,
                workspace=self.workspace.name,
                extra=self.metadata.to_dict()
            )
            return obj

    def update(self, data, context, save=True) -> TBoolStr:
        new_deployment_data = data.pop('deploy', None)
        if new_deployment_data is None:
            new_name = data.get('name')
            if new_name is not None:
                with self.resource_read(locked=False, parents_locked=False):
                    self.__manager_rename(new_name)
            return super().update(data, context, save=save)
        # we need to delete previous model and then deploy new one
        with self.resource_write(locked=False, parents_locked=False):
            name = data.get('name')
            path = data.get('path')
            deployer = BaseModelDeployer.get_by_name(new_deployment_data)
            if deployer is None:
                return False, "Deployer name is wrong or not existing."
            # First deploy new model, then delete old one (if necessary)
            result, msg = deployer.deploy_model(new_deployment_data, context, name, path)
            if not result:
                return result, f"Failed to deploy model: '{msg}'"
            # if another path is provided, delete previous model, otherwise retain it
            if self.path != path:
                self.__manager_delete()
            self.path = path    # update path
            return super().update(data, context, save=save)

    def __manager_rename(self, new_name: str) -> TBoolStr:
        manager = BaseDataManager.get()
        bdir = self.base_dir()
        path_list = self.get_path_list()
        dirs = bdir + path_list
        fname = self.name + '.pt'
        parents = dirs
        manager.rename_file(old_name=fname, parents=parents, new_name=new_name+'.pt')
        return True, None

    def __manager_delete(self) -> TBoolStr:
        manager = BaseDataManager.get()
        bdir = self.base_dir()
        path_list = self.get_path_list()
        dirs = bdir + path_list
        fname = self.name + '.pt'
        parents = dirs
        manager.delete_file(fname, parents)
        return True, None

    @auto_tboolexc
    def delete(self, context: UserWorkspaceResourceContext, locked=False, parents_locked=False) -> TBoolExc:
        with self.resource_delete(locked, parents_locked):
            try:
                db.Document.delete(self)
                self.__manager_delete()
            except Exception as ex:
                return False, ex


__all__ = [
    'MongoDeployedModelMetadata',
    'MongoDeployedModelConfig',
]