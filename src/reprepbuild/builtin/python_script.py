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
"""Execute Python scripts."""

import contextlib
import inspect
import os

import attrs

from ..command import Command
from ..utils import format_case_args, hide_path, import_python_path, load_constants

__all__ = ("python_script",)


@attrs.define
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
                "command": "rr-python-script ${in} '${argstr}' ${script_opts} > ${out}",
                "depfile": "${out_prefix}.d",
            }
        }

    def generate(self, inp: list[str], out: list[str], arg) -> tuple[list, list[str]]:
        """See Command.generate."""
        # Parse parameters
        if len(inp) < 1:
            raise ValueError(
                "Expecting one at least input file, the Python script, "
                f"and optionally some JSON files with variable. Got: {inp}"
            )
        path_py = inp[0]
        if not path_py.endswith(".py"):
            raise ValueError(f"Python script must have a .py extension. Got {path_py}")
        paths_constants = inp[1:]
        for path_constants in paths_constants:
            if not path_constants.endswith(".json"):
                raise ValueError(f"The constants files must end with .json, got {path_constants}")
        if len(out) != 0:
            raise ValueError(f"Expected no outputs, got: {out}")
        if arg is not None:
            raise ValueError(f"Expected no arguments, got {arg}")

        # Process path_py
        workdir, fn_py = os.path.split(path_py)
        workdir = os.path.normpath(workdir)
        script_prefix = fn_py[:-3]

        # Update here in a copy of constants, because scripts are always executed in their local
        # directory by convention.
        root = os.environ.get("REPREPBUILD_ROOT", os.getcwd())
        constants = load_constants(root, workdir, paths_constants)
        constants["here"] = workdir

        with contextlib.chdir(workdir):
            # Load the script in its own directory
            script = import_python_path(fn_py)

            # Handle reprepbuild_info
            reprepbuild_info = getattr(script, "reprepbuild_info", None)
            if reprepbuild_info is None:
                return ["Skipped: reprepbuild_info(...) missing"], []

            # Handle reprepbuild_cases
            reprepbuild_cases = getattr(script, "reprepbuild_cases", None)
            if reprepbuild_cases is None:
                build_cases = [[]]
            else:
                cases_kwargs = {}
                if "constants" in inspect.signature(reprepbuild_cases).parameters:
                    cases_kwargs["constants"] = constants.copy()
                build_cases = reprepbuild_cases(**cases_kwargs)
            case_fmt = getattr(script, "REPREPBUILD_CASE_FMT", None)

            def fix_path(fn_local):
                return os.path.normpath(os.path.join(workdir, fn_local))

            def get_paths(build_info, name):
                """Extract a list of paths, type check and fix."""
                paths = build_info.get(name, [])
                if not (isinstance(paths, list) and all(isinstance(item, str) for item in paths)):
                    raise TypeError(f"Field {name} must be a list of str, got {paths}.")
                return [fix_path(path) for path in paths]

            # Loop over all cases to make build records
            builds = []
            paths_log = []
            info_kwargs = {}
            for script_args in build_cases:
                # Re-assign constants to avoid passing on changes.
                if "constants" in inspect.signature(reprepbuild_info).parameters:
                    info_kwargs = {"constants": constants.copy()}
                build_info = reprepbuild_info(*script_args, **info_kwargs)
                argstr = format_case_args(script_args, script_prefix, case_fmt)
                if argstr.startswith("-"):
                    raise ValueError(f"The script argstr cannot sart with a dash, got {argstr}")
                out_prefix = hide_path(fix_path(script_prefix if argstr == "" else argstr))
                path_log = f"{out_prefix}.log"
                paths_log.append(path_log)
                build = {
                    "inputs": [path_py],
                    "implicit": get_paths(build_info, "inputs") + paths_constants,
                    "rule": "python_script",
                    "implicit_outputs": get_paths(build_info, "outputs"),
                    "outputs": [path_log],
                    "variables": {"argstr": argstr, "out_prefix": out_prefix},
                }
                if len(paths_constants) > 0:
                    build["variables"]["script_opts"] = "-c " + " ".join(paths_constants)
                builds.append(build)

            # Add a phony rule to run all cases of the script
            build = {"inputs": paths_log, "rule": "phony", "outputs": [path_py[:-3]]}
            builds.append(build)

            return builds, [path_py, *paths_constants]


python_script = PythonScript()
