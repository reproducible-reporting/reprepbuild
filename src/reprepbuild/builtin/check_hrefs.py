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
"""Check hyper references."""

from itertools import chain

import attrs
import cattrs

from ..command import Command
from ..utils import hide_path

__all__ = ("check_hrefs",)


@attrs.define
class CheckHRefsArg:
    translate: list[tuple[str, str]] = attrs.field(default=[])
    ignore: list[str] = attrs.field(default=[])


@attrs.define
class CheckHRefs(Command):
    """Check hyper references."""

    @property
    def name(self) -> str:
        """The name of the command in ``reprepbuild.yaml``."""
        return "check_hrefs"

    @property
    def rules(self) -> dict[str, dict]:
        """A dict of kwargs for Ninja's ``Writer.rule()``."""
        return {"check_hrefs": {"command": "rr-check-hrefs ${in} ${out} ${cli_args}"}}

    def generate(self, inp: list[str], out: list[str], arg) -> tuple[list, list[str]]:
        """See Command.generate."""
        # Check parameters
        if not all(path_doc.endswith(".md") or path_doc.endswith(".pdf") for path_doc in inp):
            raise ValueError(
                f"The inputs for check_hrefs must be a Markdown or PDF files, got {inp}."
            )
        if len(out) != 0:
            raise ValueError(f"Expected no outputs, got: {out}")
        cli_args = []
        if arg is not None:
            converter = cattrs.Converter(forbid_extra_keys=True)
            arg = converter.structure(arg, CheckHRefsArg)
            if len(arg.translate) > 0:
                cli_args.append("--translate")
                cli_args.extend(chain(*arg.translate))
            if len(arg.ignore) > 0:
                cli_args.append("--ignore")
                cli_args.extend(arg.ignore)

        # Write builds
        builds = []
        for inp_path in inp:
            build = {
                "rule": "check_hrefs",
                "inputs": [inp_path],
                "outputs": [hide_path(f"{inp_path}-check_hrefs.log")],
                "variables": {"cli_args": " ".join(cli_args)},
            }
            builds.append(build)
        return builds, []


check_hrefs = CheckHRefs()
