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
"""Check hyper references."""


from ..command import Command
from ..utils import hide_path

__all__ = ("check_hrefs",)


class CheckHRefs(Command):
    """Check hyper references."""

    @property
    def name(self) -> str:
        """The name of the command in ``reprepbuild.yaml``."""
        return "check_hrefs"

    @property
    def rules(self) -> dict[str, dict]:
        """A dict of kwargs for Ninja's ``Writer.rule()``."""
        return {"check_hrefs": {"command": "rr-check-hrefs ${in} ${out}"}}

    def generate(self, inp: list[str], out: list[str], arg) -> tuple[list, list[str]]:
        """See Command.generate."""
        # Check parameters
        if not all(path_doc.endswith(".md") or path_doc.endswith(".pdf") for path_doc in inp):
            raise ValueError(
                f"The inputs for check_hrefs must be a MarkDown or PDF files, got {inp}."
            )
        if len(out) != 0:
            raise ValueError(f"Expected no outputs, got: {out}")
        if arg is not None:
            raise ValueError(f"Expected no arguments, got {arg}")

        # Write builds
        builds = []
        for inp_path in inp:
            build = {
                "rule": "check_hrefs",
                "inputs": [inp_path],
                "outputs": [hide_path(f"{inp_path}-check_hrefs.log")],
            }
            builds.append(build)
        return builds, []


check_hrefs = CheckHRefs()
