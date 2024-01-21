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
"""Execute Shell scripts scripts."""

import os

import attrs

from ..command import Command

__all__ = ("shell_script",)


@attrs.define
class ShellScript(Command):
    """Execute a Shell script."""

    @property
    def name(self) -> str:
        """The name of the command in ``reprepbuild.yaml``."""
        return "shell_script"

    @property
    def rules(self) -> dict[str, dict]:
        """A dict of kwargs for Ninja's ``Writer.rule()``."""
        return {"shell_script": {"command": "rr-shell-script ${in} > ${out}"}}

    def generate(self, inp: list[str], out: list[str], arg) -> tuple[list, list[str]]:
        """See Command.generate."""
        # Parse parameters
        if len(inp) != 1:
            raise ValueError(f"Expecting one input file, the Shell script, got: {inp}")
        if len(out) != 0:
            raise ValueError(f"Expected no outputs, got: {out}")
        if arg is not None:
            raise ValueError(f"Expected no arguments, got {arg}")
        path_sh = inp[0]
        if not path_sh.endswith(".sh"):
            raise ValueError(f"Python script must have a .sh extension. Got {path_sh}")
        if not os.path.isfile(path_sh):
            raise ValueError(f"Python script does not exist: {path_sh}")

        workdir, fn_sh = os.path.split(path_sh)
        script_prefix = fn_sh[:-3]

        def fix_path(fn_local):
            return os.path.normpath(os.path.join(workdir, fn_local))

        # Deduce implicit inputs and outputs
        implicit = []
        implicit_outputs = []
        with open(path_sh) as fh:
            for line in fh:
                if line.startswith("#REPREPBUILD"):
                    words = line[12:].split()
                    keyword = words[0].lower()
                    paths = [fix_path(path) for path in words[1:]]
                    if keyword == "inputs":
                        implicit.extend(paths)
                    elif keyword == "outputs":
                        implicit_outputs.extend(paths)
                    else:
                        raise ValueError(
                            f"Unsupported Shell keyword in {path_sh}: #REPREPBUILD {keyword}"
                        )

        build = {
            "rule": "shell_script",
            "inputs": [path_sh],
            "implicit": implicit,
            "implicit_outputs": implicit_outputs,
            "outputs": [fix_path(f".{script_prefix}.log")],
        }

        return [build], [path_sh]


shell_script = ShellScript()
