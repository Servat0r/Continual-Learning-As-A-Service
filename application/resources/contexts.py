# Validation and Build contexts (user, workspace etc.)
from __future__ import annotations

from application.utils import t


class ResourceContext:

    def types(self) -> dict[type, str]:
        """
        Retrieves all registered types for this context.
        :return:
        """
        return self.types_dict.copy()

    def register_type(self, name: str):
        def registerer(cls: type):
            self.types_dict[cls] = name
            return cls
        return registerer

    def get_type_name(self, tp: type) -> str | None:
        return self.types_dict.get(tp)

    def get_types(self, name: str) -> set[type]:
        tps = self.types()
        return set(
            filter(lambda key: tps[key] == name, tps.keys())
        )

    def push(self, name: str, obj, set_type=False, type_name=None):
        self.stack.append({name: obj})
        if set_type:
            self.types_dict[obj] = type_name if type_name is not None else type(obj).__name__

    def pop(self, check_type_name=False, type_name=None) -> tuple[str, t.Any]:
        if check_type_name and (type_name is not None):
            tp = type(self.stack[-1])
            if not self.types_dict.get(tp) == type_name:
                raise TypeError(f"Incorrect typename for last element: '{tp.__name__}' against '{type_name}'.")
        result = self.stack.pop()
        return list(result.keys())[0], list(result.values())[0]

    def head(self, check_type_name=False, type_name=None) -> tuple[str, t.Any]:
        if check_type_name and (type_name is not None):
            tp = type(self.stack[-1])
            if not self.types_dict.get(tp) == type_name:
                raise TypeError(f"Incorrect typename for last element: '{tp.__name__}' against '{type_name}'.")
        result = self.stack[-1]
        return list(result.keys())[0], list(result.values())[0]

    def __init__(self):
        self.stack = []
        self.types_dict: dict[type, str] = {}


class UserResourceContext(ResourceContext):

    _DFL_USER_NAME = 'User'

    @staticmethod
    def dfl_username() -> str:
        return UserResourceContext._DFL_USER_NAME

    def register_user_type(self):
        return self.register_type(self._DFL_USER_NAME)

    def get_user_types(self) -> set[type]:
        return self.get_types(self.dfl_username())

    def get_username(self):
        return self.username

    def __init__(self, username: str, user_type: type = None, **kwargs):
        super().__init__()
        self.username = username

        if user_type is not None:
            self.register_user_type()(user_type)

        if kwargs is not None:
            self.stack.append({'kwargs': kwargs})


class UserWorkspaceResourceContext(UserResourceContext):

    _DFL_WORKSPACE_NAME = 'Workspace'

    @staticmethod
    def dfl_wname() -> str:
        return UserWorkspaceResourceContext._DFL_WORKSPACE_NAME

    def register_workspace_type(self):
        return self.register_type(self._DFL_WORKSPACE_NAME)

    def get_workspace_types(self) -> set[type]:
        return self.get_types(self.dfl_wname())

    def get_workspace(self):
        return self.workspace

    def __init__(self, username: str, workspace: str, user_type: type = None, workspace_type: type = None, **kwargs):
        super().__init__(username, user_type)
        self.workspace = workspace

        if workspace_type is not None:
            self.register_workspace_type()(workspace_type)

        if kwargs is not None:
            self.stack.append({'kwargs': kwargs})


__all__ = [
    'ResourceContext',
    'UserResourceContext',
    'UserWorkspaceResourceContext',
]