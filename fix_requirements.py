# Simple script to run in order to fix requirements.txt file for Dockerfile.
from __future__ import annotations
from typing import Callable, Sequence
from functools import wraps


_DFL_INPUT_FILE = 'requirements.txt'
_DFL_OUTPUT_FILE = 'docker_requirements.txt'


_RULES: dict[str, Callable] = {}


def rule(*modules: str):
    def matcher(f: Callable):
        for module in modules:
            _RULES[module] = f
        return f
    return matcher


def match_rule(line: str, rule_value: str):
    return line.startswith(rule_value)