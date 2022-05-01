from __future__ import annotations
import os
import shutil

from application.resources import TBoolExc
from application.models import User, Workspace
from application.data_managing import BaseDataManager


@BaseDataManager.set_class
class MongoLocalDataManager(BaseDataManager):
    """
    A data manager that uses local filesystem together with MongoDB.
    Uses Mongo ObjectIDs to create directory names.
    """

    def __init__(self, root_dir: str):
        root_dir = os.path.abspath(root_dir)
        os.makedirs(root_dir, exist_ok=True)
        self.root_dir = root_dir

    @classmethod
    def create(cls, root_dir: str = BaseDataManager._DFL_ROOT_DIR, *args, **kwargs) -> MongoLocalDataManager:
        manager = cls(root_dir)
        return manager

    def before_create_user(self, *args, **kwargs) -> TBoolExc:
        return True, None

    def after_create_user(self, user: User, *args, **kwargs) -> TBoolExc:
        user_dir = f"User_{user.get_id()}"
        print(user_dir)
        user_root_dir = os.path.join(self.root_dir, user_dir)
        try:
            os.makedirs(user_root_dir, exist_ok=True)
            # Here user must save!
            return True, None
        except Exception as ex:
            return False, ex

    def before_delete_user(self, user: User, *args, **kwargs) -> TBoolExc:
        try:
            for workspace in user.workspaces():
                result, exc = Workspace.delete(workspace)
                if not result:
                    return False, exc
            shutil.rmtree(self.get_user_root_dir(user), ignore_errors=True)
            return True, None
        except Exception as ex:
            return False, ex

    def after_delete_user(self, user: User, *args, **kwargs) -> TBoolExc:
        return True, None

    def before_create_workspace(self, *args, **kwargs) -> TBoolExc:
        return True, None

    def after_create_workspace(self, workspace: Workspace, *args, **kwargs) -> TBoolExc:
        workspace_dir = f"Workspace_{workspace.get_id()}"
        print(workspace_dir)
        workspace_root_dir = os.path.join(self.get_user_root_dir(workspace.get_owner()), workspace_dir)
        try:
            os.makedirs(workspace_root_dir, exist_ok=True)
            # Here workspace must save!
            return True, None
        except Exception as ex:
            return False, ex

    def before_delete_workspace(self, workspace: Workspace, *args, **kwargs) -> TBoolExc:
        if workspace.is_open():
            return False, RuntimeError(f"Workspace '{workspace.get_name()}' is still open!")
        try:
            # TODO Aggiungere controllo sulle risorse ancora in uso da esperimenti etc.
            shutil.rmtree(self.get_workspace_root_dir(workspace), ignore_errors=True)
            return True, None
        except Exception as ex:
            return False, ex

    def after_delete_workspace(self, workspace: Workspace, *args, **kwargs) -> TBoolExc:
        return True, None

    def get_user_root_dir(self, user: str | User) -> str:
        """
        User root directory (e.g. for use by a DataRepository).
        :param user:
        :return:
        """
        user_dir = f"User_{User.canonicalize(user).get_id()}"
        return os.path.join(self.root_dir, user_dir)

    def get_workspace_root_dir(self, workspace: Workspace) -> str:
        workspace_dir = f"Workspace_{workspace.get_id()}"
        return os.path.join(self.get_user_root_dir(workspace.get_owner()), workspace_dir)