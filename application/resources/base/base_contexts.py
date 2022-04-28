# Validation and Build contexts (user, workspace etc.)
from __future__ import annotations

from application.resources.utils import *


class ResourceContext:

    __TYPES__: TDesc = {}

    @staticmethod
    def types() -> TDesc:
        """
        Retrieves all registered types for this context.
        :return:
        """
        return ResourceContext.__TYPES__.copy()

    @staticmethod
    def register_type(name: str):
        def registerer(cls: nbr_type):
            ResourceContext.__TYPES__[name] = cls
            return cls
        return registerer

    def get_type(self, name: str) -> nbr_type | None:
        return self.types().get(name)

    def get_type_names(self, tp: nbr_type) -> set[str]:
        tps = self.types()
        return set(
            filter(lambda key: tps[key] == tp, tps.keys())
        )

    def check_names(self, names: dict[str, str]):
        return set(self.types().keys()).issubset(set(names.keys()))

    @abstractmethod
    def names_dict(self) -> dict[str, str]:
        pass

    def resource_dict(self) -> dict[str, tuple[nbr_type, str]]:
        result: dict[str, tuple[nbr_type, str]] = {}
        for item in self.names_dict().items():
            result[item[0]] = (self.types().get(item[0]), item[1])
        return result


class UserResourceContext(ResourceContext, ABC):

    _DFL_USER_NAME: str = 'user'

    @staticmethod
    def dfl_username() -> str:
        return UserResourceContext._DFL_USER_NAME

    @classmethod
    def register_user_type(cls):
        return ResourceContext.register_type(cls.dfl_username())

    def get_user_type(self) -> nbr_type | None:
        return self.get_type(self.dfl_username())

    def get_username(self):
        return self.names_dict()[self.dfl_username()]


class UserWorkspaceResourceContext(UserResourceContext, ABC):

    _DFL_WORKSPACE_NAME = 'workspace'

    @staticmethod
    def dfl_wname() -> str:
        return UserWorkspaceResourceContext._DFL_WORKSPACE_NAME

    @classmethod
    def register_workspace_type(cls):
        return ResourceContext.register_type(cls.dfl_wname())

    def get_workspace_type(self) -> nbr_type | None:
        return self.get_type(self.dfl_wname())

    def get_workspace(self):
        return self.names_dict()[self.dfl_wname()]