from __future__ import annotations
from resources import *


class DictUserResourceContext(UserResourceContext):

    def names_dict(self) -> dict[str, str]:
        return self._names

    def __init__(self, username: str, **kwargs: str):
        kwargs[self._DFL_USER_NAME] = username
        if not self.check_names(kwargs):
            raise ValueError('Missing one or more context parameters.')
        else:
            self._names = kwargs
            self._username = username

    def get_user_type(self) -> nbr_type | None:
        return self.get_type(self._DFL_USER_NAME)


class DictUserWorkspaceResourceContext(DictUserResourceContext, UserWorkspaceResourceContext):

    def __init__(self, username: str, workspace: str, **kwargs: str):
        kwargs[self.dfl_wname()] = workspace
        super().__init__(username, **kwargs)
        self._workspace = workspace

    def get_workspace_type(self) -> nbr_type | None:
        return self.get_type(self._DFL_WORKSPACE_NAME)