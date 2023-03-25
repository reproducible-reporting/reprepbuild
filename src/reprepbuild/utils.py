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
import os
import re

__all__ = (
    "parse_inputs_fls",
    "write_dep",
    "write_dyndep",
    "import_python_path",
    "check_script_args",
)


def parse_inputs_fls(path_fls):
    """Get local inputs from an fls file."""
    # Collect inputs and outputs
    workdir = os.path.dirname(path_fls)
    inputs = set()
    outputs = set()
    with open(path_fls) as f:
        for line in f:
            if line.startswith("INPUT "):
                select = inputs
                path = line[6:].strip()
            elif line.startswith("OUTPUT "):
                select = outputs
                path = line[7:].strip()
            else:
                continue
            path = os.path.normpath(path)
            if path.startswith("/"):
                continue
            path = os.path.join(workdir, path)
            select.add(path)
    # When files are both inputs and outputs, skip them.
    # These are usually aux and out.
    inputs -= outputs
    return sorted(inputs)


def filter_local_files(paths):
    """Return paths, only those under the cwd, without duplicates, sorted and normalized."""
    local = set()
    for path in paths:
        path = os.path.normpath(os.path.relpath(path))
        if not path.startswith(".."):
            local.add(path)
    return sorted(local)


def write_dep(path_dep, outputs, inputs):
    """Write a depfile for outputs that depend on inputs.

    Inputs are ignored when they are not inside of the current directory (recursively).

    It is assumed that the depfile is always specified as "depfile = $out.depfile"
    and that there is only one output file.
    """
    with open(path_dep, "w") as f:
        f.write(" ".join(outputs))
        f.write(": \\\n")
        for ipath in filter_local_files(inputs):
            f.write(f"    {ipath} \\\n")


def write_dyndep(path_dyndep, output, imp_outputs, imp_inputs):
    """Write a dynamic dependency file for ninja, for a single output."""
    with open(path_dyndep, "w") as f:
        f.write("ninja_dyndep_version = 1\n")
        f.write(f"build {output}")
        imp_outputs = filter_local_files(imp_outputs)
        if len(imp_outputs) > 0:
            f.write(" | ")
            f.write(" ".join(imp_outputs))
        f.write(": dyndep")
        imp_inputs = filter_local_files(imp_inputs)
        if len(imp_inputs) > 0:
            f.write(" | ")
            f.write(" ".join(imp_inputs))
        f.write("\n")


def import_python_path(path):
    """Return a module by importing a Python file at a given path."""
    spec = importlib.util.spec_from_file_location("<pythonscript>", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_script_args(script_args):
    for script_arg in script_args:
        if isinstance(script_arg, str):
            if not re.match(r"^[a-zA-Z0-9_-]*$", script_arg):
                raise ValueError(
                    "Script argument must only contain letters, numbers, underscores, and hyphens."
                )  # E:lin101
        elif not isinstance(script_arg, (int, float)):
            raise TypeError("A script argument must be int, float or str.")
    return "".join(f"_{script_arg}" for script_arg in script_args)
