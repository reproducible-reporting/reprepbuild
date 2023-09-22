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
"""Execute Python scripts."""

import contextlib
import os

from ..command import Command
from ..utils import format_case_args, hide_path, import_python_path

__all__ = ("python_script",)


class PythonScript(Command):
    """Execute a Python script."""

    @property
    def name(self) -> str:
        """The name of the command in ``reprepbuild.yaml``."""
        return "python_script"

    @property
    def rules(self) -> dict[str, dict]:
        """A dict of kwargs for Ninja's ``Writer.rule()``."""
        return {
            "python_script": {
                "command": "rr-python-script ${in} -- ${argstr} > ${out}",
                "depfile": "${out_prefix}.d",
            }
        }

    def generate(
        self, inp: list[str], out: list[str], arg, variables: dict[str, str]
    ) -> tuple[list, list[str]]:
        """See Command.generate."""
        # Parse parameters
        if len(inp) != 1:
            raise ValueError(f"Expecting one input file, the Python script, got: {inp}")
        if len(out) != 0:
            raise ValueError(f"Expected no outputs, got: {out}")
        if arg is not None:
            raise ValueError(f"Expected no arguments, got {arg}")
        path_py = inp[0]
        if not path_py.endswith(".py"):
            raise ValueError(f"Python script must have a .py extension. Got {path_py}")
        if not os.path.isfile(path_py):
            raise ValueError(f"Python script does not exist: {path_py}")

        # Call reprepbuild_info (and reprepbuild_cases)
        # as if the script is running in its own directory.
        workdir, fn_py = os.path.split(path_py)
        workdir = os.path.normpath(workdir)
        script_prefix = fn_py[:-3]
        with contextlib.chdir(workdir):
            # Load the script in its own directory
            pythonscript = import_python_path(fn_py)

            # Get the relevant functions
            reprepbuild_info = getattr(pythonscript, "reprepbuild_info", None)
            if reprepbuild_info is None:
                return ["Skipped: reprepbuild_info(...) missing"], []
            reprepbuild_cases = getattr(pythonscript, "reprepbuild_cases", None)
            if reprepbuild_cases is None:
                build_cases = [[]]
            else:
                build_cases = reprepbuild_cases()
            case_fmt = getattr(pythonscript, "REPREPBUILD_CASE_FMT", None)

            def fix_path(fn_local):
                return os.path.normpath(os.path.join(workdir, fn_local))

            # Loop over all cases to make build records
            builds = []
            for script_args in build_cases:
                build_info = reprepbuild_info(*script_args)
                argstr = format_case_args(script_args, script_prefix, case_fmt)
                out_prefix = hide_path(fix_path(script_prefix if argstr == "" else argstr))
                fn_log = f"{out_prefix}.log"
                implicit_inputs = [fix_path(ipath) for ipath in build_info.get("inputs", [])]
                implicit_outputs = [fix_path(opath) for opath in build_info.get("outputs", [])]
                build = {
                    "inputs": [path_py],
                    "implicit": implicit_inputs,
                    "rule": "python_script",
                    "implicit_outputs": implicit_outputs,
                    "outputs": [fn_log],
                    "variables": {"argstr": argstr, "out_prefix": out_prefix},
                }
                builds.append(build)
            return builds, []


python_script = PythonScript()
