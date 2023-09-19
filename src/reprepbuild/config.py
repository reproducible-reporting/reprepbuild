# RepRepBuild is the build tool for Reproducible Reporting.
# Copyright (C) 2023 Toon Verstraelen
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
import json
import os
import re

import attrs
import cattrs
import yaml

from .command import Command
from .fancyglob import NoFancyTemplate
from .task import Task
from .utils import CaseSensitiveTemplate

__all__ = ("load_config",)


CONVERTER = cattrs.Converter(forbid_extra_keys=True)

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
    key: (str | list[str]) = attrs.field(
        converter=_convert_key,
        validator=attrs.validators.instance_of(list),
    )
    val: (str | list[str] | list[list[str]]) = attrs.field(
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
class CommandConfig(TaskConfig):
    command: str = attrs.field(validator=attrs.validators.instance_of(str))
    inp: str = attrs.field(validator=attrs.validators.instance_of(str))
    out: str = attrs.field(
        validator=attrs.validators.optional(attrs.validators.instance_of(str)),
        default="",
    )
    arg = attrs.field(default=None)
    loop: list[LoopConfig] = attrs.field(
        validator=attrs.validators.instance_of(list),
        default=attrs.Factory(list),
    )


@attrs.define
class SubDirConfig(TaskConfig):
    subdir: str = attrs.field(validator=attrs.validators.instance_of(str))


@attrs.define
class Config:
    imports: list[str] = attrs.field(default=attrs.Factory(list))
    variables: dict[str, str] = attrs.field(default=attrs.Factory(dict))
    tasks: list[CommandConfig | SubDirConfig] = attrs.field(default=attrs.Factory(list))

    @imports.validator
    def validate_imports(self, attribute, imports):
        for module_name in imports:
            if not isinstance(module_name, str):
                raise TypeError(f"Imports must be strings, got: {module_name}")
            if RE_IMPORT.fullmatch(module_name) is None:
                raise ValueError(f"Invalid module name: {module_name}")

    @variables.validator
    def validate_variables(self, attribute, variables):
        for name, value in variables.items():
            if not isinstance(name, str):
                raise TypeError(f"Variable names must be strings, got: {name}")
            if not isinstance(value, str):
                raise TypeError(f"Variable contents must be strings, got: {value}")
            if RE_NAME.fullmatch(name) is None:
                raise ValueError(f"Invalid variable name: {name}")
            if not CaseSensitiveTemplate(value).is_valid():
                raise ValueError(f"Incorrectly formatted value of variable {name}: {value}")

    @tasks.validator
    def validate_tasks(self, attribute, tasks):
        for task in tasks:
            if not isinstance(task, TaskConfig):
                raise TypeError(f"Tasks must be TaskConfig, got: {task}")
            if isinstance(task, CommandConfig):
                if RE_NAME.fullmatch(task.command) is None:
                    raise ValueError(f"Invalid task command: {task.command}")


def load_config(
    root: str,
    path_config: str,
    tasks: list[Task],
    inherit_variables: (dict[str, str] | None) = None,
    commands: (dict[str, Command] | None) = None,
):
    """Load a RepRepBuild configuration file (recursively).

    Parameters
    ----------
    root
        The directory of the top-level ``reprepbuild.yaml`` file.
    path_config
        The path of the ``reprepbuild.yaml`` file in the current recursion.
    tasks
        The list of tasks being generated. (output parameter)
    inherit_variables
        Variables inherited from higher recursions.
    commands
        Commands inherited from higher recursions.
    """
    # Load config file into Config instance with basic validation.
    with open(os.path.join(root, path_config)) as fh:
        try:
            config = CONVERTER.structure(yaml.safe_load(fh), Config)
        except Exception as exc:
            exc.add_note(f"Error occurred while loading {path_config}")
            raise

    # Start by setting here, root and shadow built-in variables
    here = os.path.normpath(os.path.dirname(path_config))
    variables = {
        "here": here,
        "root": str(root),
    }

    # Take variables from the environment
    env_prefix = "REPREPBUILD_VARIABLE_"
    for env_name, value in os.environ.items():
        if env_name.startswith(env_prefix):
            name = env_name[len(env_prefix) :]
            if name not in variables:
                variables[name] = CaseSensitiveTemplate(value).substitute(variables)

    # Take variables from the config
    for name, value in config.variables.items():
        if name not in variables:
            variables[name] = CaseSensitiveTemplate(value).substitute(variables)

    # Finally, fill up with inherited variables, for which no substitution is needed.
    if inherit_variables is not None:
        for name, value in inherit_variables.items():
            if name not in variables:
                variables[name] = value

    # Dump variables in .reprepbuild/variables.json
    fn_variables = os.path.join(here, ".reprepbuild", "variables.json")
    write_if_changed(fn_variables, json.dumps(variables))

    # Import commands
    commands = {} if commands is None else commands.copy()
    for module_name in config.imports:
        for command in importlib.import_module(module_name).get_commands():
            if command.name == "subdir":
                raise ValueError(
                    f"In {path_config}, command subdir from {module_name} is not allowed."
                )
            commands[command.name] = command

    # Build list of tasks, expanding variables, not yet fancy glob patterns
    for task_config in config.tasks:
        if isinstance(task_config, SubDirConfig):
            load_config(
                root,
                os.path.join(here, task_config.subdir, os.path.basename(path_config)),
                tasks,
                variables,
                commands,
            )
        elif isinstance(task_config, CommandConfig):
            command_name = task_config.command
            if command_name.startswith("_"):
                default = False
                command_name = command_name[1:]
            else:
                default = True
            command = commands.get(command_name)
            if command is None:
                raise ValueError(f"In {path_config}, unknown command: {command_name}")
            for loop_variables in iterate_loop_config(task_config.loop):
                task = Task(
                    command,
                    default,
                    variables,
                    _parse_paths(task_config.inp, variables | loop_variables),
                    _parse_paths(task_config.out, variables | loop_variables),
                    task_config.arg,
                )
                tasks.append(task)
        else:
            raise TypeError(f"Cannot use task_config of type {type(task_config)}: {task_config}")


def write_if_changed(filename: str, contents: str) -> bool:
    """Write a file if the contents are new."""
    if os.path.exists(filename):
        with open(filename) as fh:
            if fh.read() == contents:
                return False
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as fh:
        fh.write(contents)
    return True


def _parse_paths(paths_string: str, variables: dict[str, str]) -> list[str]:
    """Process paths in the config file: substitue vars and write relative to root.

    Parameters
    ----------
    paths_string
        A string containing one or more paths, separated by whitespace
    variables
        The variables to be substituted.
        Missing variables will raise an error, unless they are named wildcards, like ``${*name}``.

    Returns
    -------
    paths
        A list of paths without variable references.
    """
    result = []
    for path0 in NoFancyTemplate(paths_string).substitute_nofancy(variables).split():
        if path0.startswith(os.sep):
            path1 = os.path.normpath(os.path.relpath(path0, variables["root"]))
        else:
            path1 = os.path.normpath(os.path.join(variables["here"], path0))
        if path0.endswith(os.sep):
            path1 += os.sep
        result.append(path1)
    return result
