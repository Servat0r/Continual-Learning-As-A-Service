"""
Validation functions for url elements (username, password, workspace/resource/experiment name,
allowed data repository paths etc.)
"""
from __future__ import annotations
from pyisemail import is_email

from .utils import TBoolStr


# Validation help
def _not_none(subject: str) -> str:
    return f"{subject} must be not None."


def _not_empty(subject: str) -> str:
    return f"{subject} must be not empty."


def _min_chars(subject: str, min_chars: int) -> str:
    return f"{subject} must have at least {min_chars} characters."


def _max_chars(subject: str, max_chars: int) -> str:
    return f"{subject} must have at most {max_chars} characters."


def _requirements(subject: str, desc: str) -> str:
    return f"{subject} must contain {desc}."


def base_validation_function(
        value: str, subject: str, min_chars: int = None,
        max_chars: int = None, not_empty: bool = True,
) -> TBoolStr:
    if value is None:
        return False, _not_none(subject)
    elif not_empty and len(value) == 0:
        return False, _not_empty(subject)
    elif (min_chars is not None) and (len(value) < min_chars):
        return False, _min_chars(subject, min_chars)
    elif (max_chars is not None) and (len(value) > max_chars):
        return False, _max_chars(subject, max_chars)
    else:
        return True, None


# Username validation
USERNAME_MIN_CHARS = 1
USERNAME_MAX_CHARS = 64
_USERNAME_REQS = \
    "Username must contain only alphanumeric characters and hyphens and cannot have multiple consecutive hyphens."


def validate_username(username: str) -> TBoolStr:
    result, msg = base_validation_function(username, "Username", USERNAME_MIN_CHARS, USERNAME_MAX_CHARS)
    if not result:
        return result, msg
    else:
        ulen = len(username)
        for index in range(ulen):
            curr_char = username[index]
            if (not curr_char.isalnum()) and (curr_char != '-'):
                return False, _USERNAME_REQS
            elif (curr_char == '-') and (index < ulen - 1):
                if username[index + 1] == '-':
                    return False, _USERNAME_REQS
        return True, None


# Email validation
def validate_email(email: str, check_dns: bool = False) -> TBoolStr:
    try:
        result = is_email(email, check_dns)
        if result:
            return result, None
        else:
            return result, 'Email validation failed.'
    except Exception as ex:
        return False, f'Error when validating email: {ex.__class__.__name__}'


# Password validation
PASSWORD_MIN_CHARS = 8
SPECIALS = ['$', '%', '&', '?', '@', '#']
_PASSWORD_REQS = \
    f"Password must have at least: {PASSWORD_MIN_CHARS} characters; a digit; an uppercase character;" \
    f" a lowercase character; a special character among {SPECIALS}."


def validate_password(password: str) -> TBoolStr:
    """
    Checks if provided password (for registering or changing password) satisfies password requirements:
    password must have at least:
        1.  8 characters;
        2.  a digit;
        3.  an uppercase character;
        4.  a lowercase character;
        5.  a special character among ['$', '%', '&', '?', '@', '#'].
    :param password:
    :return:
    """
    result, msg = base_validation_function(password, "Password", PASSWORD_MIN_CHARS)
    if not result:
        return result, msg
    else:
        digit = False
        upper = False
        lower = False
        special = False
        for char in password:
            if (not digit) and char.isdigit():
                digit = True
            elif (not lower) and char.islower():
                lower = True
            elif (not upper) and char.isupper():
                upper = True
            elif (not special) and char in SPECIALS:
                special = True
        result = upper and lower and special
        if result:
            return result, None
        else:
            return result, _PASSWORD_REQS


# Workspace/Resource/Experiment validation (names for: workspaces, data repositories, resources)
_WORKSPACE_RESOURCE_EXPERIMENT_DESC = \
    f"Workspace/DataRepository/Resource/Experiment name must contain only alphanumeric characters, hyphens (-)" \
    f" and underscores (_), and cannot contain multiple consecutive characters among the latter ones."


def validate_workspace_resource_experiment(name: str) -> TBoolStr:
    result, msg = base_validation_function(name, "Workspace/Experiment")
    if not result:
        return result, msg
    else:
        specials = ['-', '_']
        wlen = len(name)
        for index in range(wlen):
            char = name[index]
            if (not char.isalnum()) and (char not in specials):
                return False, _WORKSPACE_RESOURCE_EXPERIMENT_DESC
            elif (char in specials) and (index < wlen - 1):
                nextchar = name[index+1]
                if nextchar in specials:
                    return False, _WORKSPACE_RESOURCE_EXPERIMENT_DESC
        return True, None


# Datasets, Benchmarks, Metrics
ALNUM_MIN_CHARS = 4
ALNUM_MAX_CHARS = 64
_ALNUM_DESC = "This identifier must contain only alphanumeric characters."


def validate_alnum(alnum: str) -> TBoolStr:
    result, msg = base_validation_function(alnum, 'This identifier', ALNUM_MIN_CHARS, ALNUM_MAX_CHARS)
    if not result:
        return result, msg
    elif not alnum.isalnum():
        return False, _ALNUM_DESC
    else:
        return True, None


def validate_path(path: str) -> TBoolStr:
    result, msg = base_validation_function(path, "Path", not_empty=False)
    if not result:
        return result, msg
    else:
        forbidden = ['<', '>', ':', '"', '\\', '|', '?', '*']  # Windows compliant (for printable chars)
        for char in path:
            if char in forbidden:
                return False, f"Pathnames cannot contain a '{char}' character."
        return True, None


__all__ = [
    'base_validation_function',

    'USERNAME_MAX_CHARS',
    'USERNAME_MIN_CHARS',
    'validate_username',

    'validate_email',

    'PASSWORD_MIN_CHARS',
    'SPECIALS',
    'validate_password',

    'validate_workspace_resource_experiment',

    'ALNUM_MAX_CHARS',
    'ALNUM_MIN_CHARS',
    'validate_alnum',

    'validate_path',
]