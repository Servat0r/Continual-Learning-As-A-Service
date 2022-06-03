# Simple script to run in order to fix requirements.txt file for Dockerfile.
from __future__ import annotations

import sys
import traceback
from typing import Sequence, Callable, TextIO


_DFL_INPUT_FILE = 'input_requirements.txt'
_DFL_OUTPUT_FILE = 'output_requirements.txt'


_RULES: dict[str, Callable] = {}


def rule(*modules: str):
    def matcher(f: Callable):
        for module in modules:
            _RULES[module] = f
        return f
    return matcher


def match_rule(line: str, rule_value: str):
    return line.startswith(rule_value)


# noinspection PyUnusedLocal
@rule('torch', 'torchvision', 'torchaudio', 'torchmetrics', 'pytorchcv')
def skip_requirement(line: str):
    return False, None  # do not write anything


# noinspection PyShadowingNames
def fix_requirements(src_file: str | TextIO, dest_file: str | TextIO, append=False):
    src_str, dest_str = isinstance(src_file, str), isinstance(dest_file, str)
    try:
        if src_str:
            src_file = open(src_file, 'r')

        if dest_str:
            dest_file = open(dest_file, 'a' if append else 'w')

        for line in src_file:
            print(line)
            line = line.strip()
            print(line)
            rule_matched = False
            for rule_name, rule_func in _RULES.items():
                if match_rule(line, rule_name):
                    rule_matched = True
                    result, to_write = rule_func(line)
                    if result:
                        print(to_write, file=dest_file)
                    break
            if not rule_matched:
                print(line, file=dest_file)
        return True, None
    except Exception as ex:
        return False, ex
    finally:
        if src_str:
            src_file.close()
        if dest_str:
            dest_file.close()


def create_args_dict(argv: Sequence[str]) -> dict[str, str]:
    # noinspection PyShadowingNames
    args: dict[str, str] = {}
    for arg in argv:
        arg_name, arg_value = arg.split('=')[:2]
        args[arg_name] = arg_value
    return args


if __name__ == '__main__':
    args = create_args_dict(sys.argv[1:])

    src_file = args.get('src_file', _DFL_INPUT_FILE)
    dest_file = args.get('dest_file', _DFL_OUTPUT_FILE)
    print(f'src_file = {src_file}\ndest_file = {dest_file}')

    result, ex = fix_requirements(src_file, dest_file)
    if not result:
        print(ex)
        traceback.print_exception(*sys.exc_info())
    exit(0 if result else 1)