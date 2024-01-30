# RepRepBuild is the build tool for Reproducible Reporting.
# Copyright (C) 2024 Toon Verstraelen
#
# This file is part of RepRepBuild.
#
# RepRepBuild is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# RepRepBuild is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
#
# --
"""Load and Validate ``reprepbuild.yaml`` configuration files."""

import importlib
import os
import re
from warnings import warn

import attrs
import cattrs
import yaml

from .generator import BarrierGenerator, BaseGenerator, BuildGenerator
from .nameglob import NoNamedTemplate
from .utils import load_constants

__all__ = ("load_config", "rewrite_path")


RE_IMPORT = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*")
RE_NAME = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")


@attrs.define
class TaskConfig:
    pass


def _convert_key(key):
    return key.split() if isinstance(key, str) else key


def _convert_val(val):
    if isinstance(val, str):
        val = val.split()
    return [item.split() if isinstance(item, str) else item for item in val]


@attrs.define
class LoopConfig:
    key: str | list[str] = attrs.field(
        converter=_convert_key,
        validator=attrs.validators.instance_of(list),
    )
    val: str | list[str] | list[list[str]] = attrs.field(
        converter=_convert_val,
        validator=attrs.validators.instance_of(list),
    )

    @key.validator
    def _validate_key(self, attribute, key):
        if not all(isinstance(item, str) for item in key):
            raise TypeError("A loop 'key' must consist of strings, got: {key}")

    @val.validator
    def _validate_val(self, attribute, val):
        for item0 in val:
            if not isinstance(item0, list):
                raise TypeError(f"Item in loop 'val' must be a list, got: {item0}")
            if not all(isinstance(item1, str) for item1 in item0):
                raise TypeError(f"Item in loop 'val' must be a list of strings, got: {item0}")
            if not len(item0) == len(self.key):
                raise TypeError(f"Item in loop 'val' must have same length as 'key', got: {item0}")


def iterate_loop_config(loop: list[LoopConfig]):
    if len(loop) == 0:
        yield {}
    else:
        for val_item in loop[0].val:
            variables = dict(zip(loop[0].key, val_item, strict=True))
            for other_variables in iterate_loop_config(loop[1:]):
                yield variables | other_variables


@attrs.define
class BuildConfig(TaskConfig):
    command: str = attrs.field(validator=attrs.validators.instance_of(str))
    inp: str = attrs.field(validator=attrs.validators.instance_of(str))
    out: str = attrs.field(validator=attrs.validators.instance_of(str), default="")
    arg = attrs.field(default=None)
    loop: list[LoopConfig] = attrs.field(
        validator=attrs.validators.instance_of(list),
        default=attrs.Factory(list),
    )
    override: dict[str, str] = attrs.field(
        validator=attrs.validators.instance_of(dict), default=attrs.Factory(dict)
    )
    built_inputs_only: bool = attrs.field(converter=bool, default=False)
    default: bool = attrs.field(converter=bool, default=True)
    optional: bool = attrs.field(converter=bool, default=False)

    def __attrs_post_init__(self):
        if self.command.startswith("_"):
            warn(
                "Prefixing commands with underscores is deprecated. Use 'default: false` instead. "
                "Support for the underscore prefix will be dropped after Februari 2024.",
                stacklevel=0,
            )
            self.command = self.command[1:]
            self.default = False


@attrs.define
class SubDirConfig(TaskConfig):
    subdir: str = attrs.field(validator=attrs.validators.instance_of(str))


@attrs.define
class BarrierConfig(TaskConfig):
    barrier: str = attrs.field(validator=attrs.validators.instance_of(str))


@attrs.define
class Config:
    imports: list[str] = attrs.field(default=attrs.Factory(list))
    tasks: list[BuildConfig | SubDirConfig | BarrierConfig] = attrs.field(
        default=attrs.Factory(list)
    )

    @imports.validator
    def validate_imports(self, attribute, imports):
        for module_name in imports:
            if not isinstance(module_name, str):
                raise TypeError(f"Imports must be strings, got: {module_name}")
            if RE_IMPORT.fullmatch(module_name) is None:
                raise ValueError(f"Invalid module name: {module_name}")

    @tasks.validator
    def validate_tasks(self, attribute, tasks):
        for task in tasks:
            if not isinstance(task, TaskConfig):
                raise TypeError(f"Tasks must be TaskConfig, got: {task}")
            if isinstance(task, BuildConfig):
                if RE_NAME.fullmatch(task.command) is None:
                    raise ValueError(f"Invalid task command: {task.command}")


def load_config(
    root: str,
    path_config: str,
    paths_constants: list[str],
    generators: list[BaseGenerator],
    phony_deps: set[str] | None = None,
):
    """Load a RepRepBuild configuration file (recursively).

    Parameters
    ----------
    root
        The directory containing the top-level ``reprepbuild.yaml``.
    path_config
        The path of the ``reprepbuild.yaml`` file in the current recursion.
    generators
        The list of generators being generated. (output parameter)
    paths_constants
        List of files with constants.
    phony_deps
        Phony dependencies imposed by previous barrier commands.
    """
    workdir, fn_config = os.path.split(path_config)
    constants = load_constants(root, workdir, paths_constants)

    # Load config file into Config instance with basic validation.
    converter = cattrs.Converter(forbid_extra_keys=True)
    with open(path_config) as fh:
        try:
            config = converter.structure(yaml.safe_load(fh), Config)
        except Exception as exc:
            exc.add_note(f"Error occurred while loading {path_config}")
            raise

    # Import commands
    commands = {}
    for module_name in config.imports:
        for command in importlib.import_module(module_name).get_commands():
            if command.name == "subdir":
                raise ValueError(
                    f"In {path_config}, command subdir from {module_name} is not allowed."
                )
            commands[command.name] = command

    # Build list of tasks, expanding paths, not yet named glob patterns
    if phony_deps is None:
        phony_deps = set()
    for task_config in config.tasks:
        if isinstance(task_config, SubDirConfig):
            load_config(
                root,
                os.path.join(workdir, task_config.subdir, fn_config),
                paths_constants,
                generators,
                phony_deps,
            )
        elif isinstance(task_config, BuildConfig):
            command = commands.get(task_config.command)
            if command is None:
                raise ValueError(f"In {path_config}, unknown command: {task_config.command}")
            for loop_variables in iterate_loop_config(task_config.loop):
                command_constants = constants.copy()
                command_constants |= task_config.override
                command_constants |= loop_variables
                generator = BuildGenerator(
                    command=command,
                    inp=rewrite_paths(task_config.inp, command_constants, True),
                    out=rewrite_paths(task_config.out, command_constants, True),
                    arg=task_config.arg,
                    constants=command_constants,
                    default=task_config.default,
                    optional=task_config.optional,
                    built_inputs_only=task_config.built_inputs_only,
                    phony_deps=list(phony_deps),
                )
                generators.append(generator)
        elif isinstance(task_config, BarrierConfig):
            phony = task_config.barrier
            if phony in phony_deps:
                raise ValueError(f"Barrier name used twice: {phony}")
            generators.append(BarrierGenerator(phony))
            phony_deps.add(phony)
        else:
            raise TypeError(f"Cannot use task_config of type {type(task_config)}: {task_config}")


def rewrite_paths(
    paths_string: str, variables: dict[str, str], ignore_wild: bool = False
) -> list[str]:
    """Process paths in the config file: substitute vars and write relative to root."""
    return [rewrite_path(path, variables, ignore_wild) for path in paths_string.split()]


def rewrite_path(path: str, variables: dict[str, str], ignore_wild: bool = False) -> str:
    """Process path in the config file: substitute vars and write relative to root.

    Parameters
    ----------
    path
        The path to rewrite.
    variables
        The variables to be substituted.
        Missing variables will raise an error.
    ignore_wild
        If true, named wildcards like ``${*name}`` are left untouched.

    Returns
    -------
    rewritten
        The rewritten path
    """
    if ignore_wild:
        path_template = NoNamedTemplate(path)
    else:
        path_template = NoNamedTemplate(path)
    if not path_template.is_valid():
        raise ValueError(f"Invalid path template string: {path}")
    if ignore_wild:
        result = path_template.substitute_nonamed(variables)
    else:
        result = path_template.substitute(variables)
    if result.startswith(os.sep):
        result = os.path.normpath(os.path.relpath(result, variables["root"]))
    else:
        result = os.path.normpath(os.path.join(variables["here"], result))
    if path.endswith(os.sep):
        result += os.sep
    return result
