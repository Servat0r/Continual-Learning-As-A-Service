from __future__ import annotations

from application.utils import TDesc, TBoolStr, abstractmethod
from application.resources.contexts import ResourceContext


class BaseModelDeployer:
    """
    Base class for deploying models.
    """
    __CONFIGS__: TDesc = {}

    @staticmethod
    def register_model_deployer(name: str = None):
        def registerer(cls):
            nonlocal name
            if name is None:
                name = cls.__name__
            BaseModelDeployer.__CONFIGS__[name] = cls
            return cls

        return registerer

    @classmethod
    def get_by_name(cls, name: str | TDesc) -> BaseModelDeployer | None:
        if isinstance(name, str):
            return cls.__CONFIGS__.get(name)
        elif isinstance(name, dict):
            cname = name.get('name')
            if cname is None:
                raise ValueError('Missing name')
            else:
                return cls.__CONFIGS__.get(cname)

    @classmethod
    def get_key(cls) -> str | None:
        for name, cl in cls.__CONFIGS__.items():
            if cls == cl:
                return name
        return None

    @classmethod
    @abstractmethod
    def validate_input(cls, data: TDesc, context: ResourceContext) -> TBoolStr:
        pass

    @classmethod
    @abstractmethod
    def deploy_model(cls, data: TDesc, context: ResourceContext, name: str, path: str) -> TBoolStr:
        pass


__all__ = [
    'BaseModelDeployer',
]