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
"""Utilities used in other parts of RepRepBuild.

The `write_depfile` and `write_dyndep` are used to specify *implicit* dependencies
which are not known when preparing the `build.ninja` file.
The adjective implicit means that these files are not command-line arguments of the build software.
Instead, they are determined on the fly by the build software or related tools.
The two mechanisms are subtly different:

- A `depfile` is used for dependencies on user-provided files only.
  These dependencies are already sitting in the source tree before ninja is called.
- A `dyndep` is used for dependencies on user-provided files and outputs of other build statements.
  The latter category of files can be the result of other build statements.
  Furthermore, a `dyndep` may also specify additional outputs besides the one that is hardwired
  in the `build.ninja` file.

A `dyndep` is more powerful and general, but also a bit more complicated to set up.
"""


import importlib.util
import json
import os
import re
import string
import sys
from collections.abc import Collection

from parse import parse

__all__ = (
    "parse_inputs_fls",
    "hide_path",
    "write_dep",
    "write_dyndep",
    "import_python_path",
    "format_case_args",
    "parse_case_args",
    "CaseSensitiveTemplate",
    "load_constants",
)


def parse_inputs_fls(path_fls: str) -> list[str]:
    """Get local inputs from an LaTeX fls file.

    Parameters
    ----------
    path_fls
        The location of the file list file.

    Returns
    -------
    paths
        A list of paths.
    """
    # Collect inputs and outputs
    workdir = os.path.dirname(path_fls)
    inputs = set()
    outputs = set()
    with open(path_fls) as f:
        for line in f:
            if line.startswith("INPUT "):
                select = inputs
                my_path = line[6:].strip()
            elif line.startswith("OUTPUT "):
                select = outputs
                my_path = line[7:].strip()
            else:
                continue
            my_path = os.path.normpath(my_path)
            if my_path.startswith("/"):
                continue
            my_path = os.path.join(workdir, my_path)
            select.add(my_path)
    # When files are both inputs and outputs, skip them.
    # These are usually aux and out.
    inputs -= outputs
    return sorted(inputs)


def hide_path(visible_path: str) -> str:
    parent, name = os.path.split(visible_path)
    if not name.startswith("."):
        name = "." + name
    return os.path.join(parent, name)


def _filter_local_files(all_paths: Collection[str]) -> list[str]:
    """Return only those paths under the cwd, without duplicates, sorted and normalized."""
    local = set()
    for any_path in all_paths:
        any_path = os.path.normpath(os.path.relpath(any_path))
        if not any_path.startswith(".."):
            local.add(any_path)
    return sorted(local)


def write_dep(path_dep: str, outputs: Collection[str], inputs: Collection[str]):
    """Write a depfile for outputs that depend on inputs.

    Inputs are ignored when they are not inside of the current directory (recursively).

    It is assumed that the depfile is always specified as "depfile = $out.depfile"
    and that there is only one output file.
    """
    with open(path_dep, "w") as f:
        f.write(" ".join(outputs))
        f.write(": \\\n")
        for ipath in _filter_local_files(inputs):
            f.write(f"    {ipath} \\\n")


def write_dyndep(path_dyndep: str, output: str, imp_outputs: list[str], imp_inputs: list[str]):
    """Write a dynamic dependency file for ninja, for a single output.

    Parameters
    ----------
    path_dyndep
        The file to write to
    output
        The output whose dependencies are dynamic.
    imp_outputs
        Implicit outputs (dynamic) produced along output.
    imp_inputs
        Implicit inputs (dynamic) required to build output.
    """
    with open(path_dyndep, "w") as f:
        f.write("ninja_dyndep_version = 1\n")
        f.write(f"build {output}")
        imp_outputs = _filter_local_files(imp_outputs)
        if len(imp_outputs) > 0:
            f.write(" | ")
            f.write(" ".join(imp_outputs))
        f.write(": dyndep")
        imp_inputs = _filter_local_files(imp_inputs)
        if len(imp_inputs) > 0:
            f.write(" | ")
            f.write(" ".join(imp_inputs))
        f.write("\n")


def import_python_path(path):
    """Return a module by importing a Python file at a given path."""
    cwd = os.getcwd()
    sys.path.append(cwd)
    spec = importlib.util.spec_from_file_location("<pythonscript>", path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(cwd)
    return module


def format_case_args(
    script_args: list | dict | tuple[list, dict], prefix: str, case_fmt: str | None = None
):
    """Format arguments for a Python script.

    Parameters
    ----------
    script_args
        Arguments for the script, can be in multiple forms.
    prefix
        The script prefix, used to generate a suitable case_fmt,
        if not given.
    case_fmt
        A formatting string to turn the args into one contiguous string.

    Returns
    -------
    argstr
        A formatted string representation of the script arguments,
        without whitespaces.
    """
    # Compatibility with old API.
    check_underscores = False
    if case_fmt is None:
        check_underscores = True
        case_fmt = prefix + "".join(["_{}"] * len(script_args))

    # Interpret the yield value of reprepbuild_cases as args and kwargs.
    args = []
    kwargs = {}
    if isinstance(script_args, list | tuple):
        if (
            len(script_args) == 2
            and isinstance(script_args[0], list | tuple)
            and isinstance(script_args[1], dict)
        ):
            args, kwargs = script_args
        else:
            args = script_args
    elif isinstance(script_args, dict):
        kwargs = script_args
    else:
        args = [script_args]

    # Check validity of kwargs
    if not all(isinstance(key, str) for key in kwargs):
        raise ValueError("Keys of kwargs must be strings.")

    # Format and check
    result = case_fmt.format(*args, **kwargs)
    if check_underscores and result[len(prefix) :].count("_") != len(script_args):
        raise ValueError(
            "When using underscores in script arguments, "
            f"specify a REPREPBUILD_CASE_FMT. ({prefix})"
        )
    if " " in result:
        raise ValueError("Script arguments cannot contain whitespace.")
    return result


def parse_case_args(argstr: str, prefix: str, case_fmt: str | None = None) -> tuple[list, dict]:
    """The inverse of format_case_args.

    Parameters
    ----------
    argstr
        The output of format_case_args.
    prefix
        The script prefix, used to generate a suitable case_fmt,
        if not given.
    case_fmt
        A formatting string to turn the args into one contiguous string.

    Returns
    -------
    args, kwargs
        Arguments and keyword arguments, to be passed into the main function of the script.
    """
    convert = False
    if case_fmt is None:
        convert = True
        suffix = argstr[len(prefix) :]
        case_fmt_suffix = "".join(["_{}"] * suffix.count("_"))
        result = parse(case_fmt_suffix, suffix, case_sensitive=True)
        if result is None:
            raise ValueError(
                f"Could not parse argstr '{suffix}' with case_fmt '{case_fmt_suffix}'."
            )
    else:
        result = parse(case_fmt, argstr, case_sensitive=True)
        if result is None:
            raise ValueError(f"Could not parse argstr '{argstr}' with case_fmt '{case_fmt}'.")
    if convert:
        args = tuple(_naive_convert(word) for word in result.fixed)
    else:
        args = result.fixed
    return args, result.named


def _naive_convert(word: str) -> int | float | str:
    """Convert str to int or float if possible."""
    for dtype in int, float:
        try:
            return dtype(word)
        except ValueError:
            pass
    return word


class CaseSensitiveTemplate(string.Template):
    """A case sensitive Template class."""

    flags = re.NOFLAG


def load_constants(root: str, cwd: str, paths_constants) -> dict[str:str]:
    """Load user-defined constant strings.

    Two special constants cannot be overridden: ``root`` and ``here``.
    ``here`` is computed as the relative path from ``root`` to the current working directory.
    Each constant definition can make use of previously defined constants,

    Parameters
    ----------
    root
        The directory containing the top-level reprepbuild.yaml file.
    cwd
        The current working directory to use when computing the ``here`` constant.
    paths_constants
        paths of JSON files containing constants.

    Returns
    -------
    constants
        A dictionary with constants.
    """
    # Special constants
    constants = {"root": root, "here": os.path.relpath(cwd, root)}
    forbidden = ["root", "here"]

    # Load from JSON files.
    for path_json in paths_constants:
        path_json = path_json.strip()
        if path_json == "":
            continue
        with open(path_json) as fh:
            this_result = json.load(fh)
        if not isinstance(this_result, dict):
            raise TypeError(f"The file {path_json} does not contain a dictionary.")
        for name, value in this_result.items():
            if name in forbidden:
                raise ValueError(f"Cannot override {name} (defined in {path_json})")
            if not isinstance(value, str):
                raise TypeError(f"Constants must be strings. Got  in {path_json}.")
            value_template = CaseSensitiveTemplate(value)
            if not value_template.is_valid():
                raise ValueError(f"Invalid template string {name}={value} in {path_json}")
            constants[name] = value_template.substitute(constants)

    return constants
