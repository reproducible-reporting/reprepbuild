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
"""Make reproducible ZIP archives."""


from ..command import Command

__all__ = ("repro_zip", "repro_latex_zip")


class ReproZip(Command):
    """Create a Reproducible Zip file."""

    @property
    def name(self) -> str:
        """The name of the command in ``reprepbuild.yaml``."""
        return "repro_zip"

    @property
    def rules(self) -> dict[str, dict]:
        """A dict of kwargs for Ninja's ``Writer.rule()``."""
        return {"repro_zip": {"command": "rr-zip ${in} ${out}"}}

    def generate(self, inp: list[str], out: list[str], arg) -> tuple[list, list[str]]:
        """See Command.generate."""
        # Check parameters
        if len(inp) != 1:
            raise ValueError(f"Expecting one input, the sha256 file, got: {inp}")
        path_sha256 = inp[0]
        if not path_sha256.endswith(".sha256"):
            raise ValueError(
                f"The input of the repro_zip command must end with .sha256, got {path_sha256}."
            )
        if len(out) != 1:
            raise ValueError(f"Expecting one output, the zip file, got: {out}")
        path_zip = out[0]
        if not path_zip.endswith(".zip"):
            raise ValueError(
                f"The output of the repro_zip command must end with .zip, got {path_zip}."
            )
        if arg is not None:
            raise ValueError(f"Expected no arguments, got {arg}")

        # Write builds
        builds = [
            {"outputs": [path_zip], "rule": "repro_zip", "inputs": [path_sha256], "pool": "console"}
        ]
        return builds, []


class ReproLatexZip(Command):
    """Create a Reproducible Zip file of a LaTeX source."""

    @property
    def name(self) -> str:
        """The name of the command in ``reprepbuild.yaml``."""
        return "repro_latex_zip"

    @property
    def rules(self) -> dict[str, dict]:
        """A dict of kwargs for Ninja's ``Writer.rule()``."""
        return {"repro_latex_zip": {"command": "rr-latex-zip ${in} ${out}"}}

    def generate(self, inp: list[str], out: list[str], arg) -> tuple[list, list[str]]:
        """See ``Command.generate``."""
        # Check parameters
        if len(inp) != 1:
            raise ValueError(f"Expecting one input, the LaTeX fls file, got: {inp}")
        path_fls = inp[0]
        if not path_fls.endswith(".fls"):
            raise ValueError(f"The input latex_zip command must end with .fls, got {path_fls}.")
        if len(out) != 1:
            raise ValueError(f"Expecting one output, the zip file, got: {out}")
        path_zip = out[0]
        if not path_zip.endswith(".zip"):
            raise ValueError(
                f"The output of the repro_zip command must end with .zip, got {path_zip}."
            )
        if arg is not None:
            raise ValueError(f"Expected no arguments, got {arg}")

        # Write builds
        builds = [
            {
                "outputs": [path_zip],
                "rule": "repro_latex_zip",
                "inputs": [path_fls],
                # Wait until the fls file is overwritten by the last LaTeX compile.
                "order_only": [path_fls[:-4] + ".pdf"],
                "pool": "console",
            }
        ]
        return builds, []


repro_zip = ReproZip()
repro_latex_zip = ReproLatexZip()
