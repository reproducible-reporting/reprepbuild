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
"""Rendering of text files with Jinja."""


import os

import attrs

from ..command import Command

__all__ = ("render",)


@attrs.define
class Render(Command):
    @property
    def name(self) -> str:
        """The name of the command in ``reprepbuild.yaml``."""
        return "render"

    @property
    def rules(self) -> dict[str, dict]:
        """A dict of kwargs for Ninja's ``Writer.rule()``."""
        return {"render": {"command": "rr-render ${in} ${out}"}}

    def generate(self, inp: list[str], out: list[str], arg) -> tuple[list, list[str]]:
        """See Command.generate."""
        # Check parameters
        if len(out) != 1:
            raise ValueError(f"Expecting one output (file or dir), got {len(out)}: {out}")
        path_out = out[0]
        if len(inp) <= 1:
            raise ValueError(
                "At least two inputs are required (template and one or more constants JSON), "
                f"got {inp}"
            )
        path_template = inp[0]
        paths_constants = inp[1:]
        for path_constants in paths_constants:
            if not path_constants.endswith(".json"):
                raise ValueError(f"The constants files must end with .json, got {path_constants}")
        if arg is not None:
            raise ValueError(f"Expected no arguments, got {arg}")

        # Determine file destination
        if path_out.endswith(os.sep):
            path_out = os.path.join(path_out, os.path.basename(path_template))

        # Create build
        build = {
            "rule": "render",
            "outputs": [path_out],
            "inputs": inp,
        }
        return [build], []


render = Render()
