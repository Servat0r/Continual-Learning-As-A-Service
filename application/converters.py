from .validation import *
from werkzeug.routing import BaseConverter, ValidationError as WerkzeugValidationError


class UsernameConverter(BaseConverter):

    def to_python(self, value: str):
        result, msg = validate_username(value)
        if result:
            return value
        else:
            raise WerkzeugValidationError(msg)

    def to_url(self, value) -> str:
        return BaseConverter.to_url(self, value)


class WorkspaceExperimentConverter(BaseConverter):

    def to_python(self, value: str):
        result, msg = validate_workspace_resource_experiment(value)
        if result:
            return value
        else:
            raise WerkzeugValidationError(msg)

    def to_url(self, value) -> str:
        return BaseConverter.to_url(self, value)


class AlphaNumConverter(BaseConverter):

    def to_python(self, value: str):
        result, msg = validate_alnum(value)
        if result:
            return value
        else:
            raise WerkzeugValidationError(msg)

    def to_url(self, value) -> str:
        return BaseConverter.to_url(self, value)


class AllowedPathConverter(BaseConverter):

    def to_python(self, value: str):
        result, msg = validate_path(value)
        if result:
            return value
        else:
            raise WerkzeugValidationError(msg)

    def to_url(self, value) -> str:
        return BaseConverter.to_url(self, value)


__all__ = [
    'UsernameConverter',
    'WorkspaceExperimentConverter',
    'AlphaNumConverter',
    'AllowedPathConverter',
    'WerkzeugValidationError',
]