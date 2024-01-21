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
"""Make reproducible ZIP archives."""


import attrs

from ..command import Command
from ..scripts.zip_plain import get_path_manifest as get_path_manifest_plain

__all__ = ("zip_manifest", "zip_latex", "zip_plain")


@attrs.define
class ZipManifest(Command):
    """Create a Reproducible Zip file."""

    @property
    def name(self) -> str:
        """The name of the command in ``reprepbuild.yaml``."""
        return "zip_manifest"

    @property
    def rules(self) -> dict[str, dict]:
        """A dict of kwargs for Ninja's ``Writer.rule()``."""
        return {"zip_manifest": {"command": "rr-zip-manifest ${in} ${out}"}}

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
        build = {
            "outputs": [path_zip],
            "rule": "zip_manifest",
            "inputs": [path_sha256],
            "pool": "console",
        }
        return [build], []


@attrs.define
class ZipLatex(Command):
    """Create a Reproducible Zip file of a LaTeX source."""

    @property
    def name(self) -> str:
        """The name of the command in ``reprepbuild.yaml``."""
        return "zip_latex"

    @property
    def rules(self) -> dict[str, dict]:
        """A dict of kwargs for Ninja's ``Writer.rule()``."""
        return {"zip_latex": {"command": "rr-zip-latex ${in} ${out}"}}

    def generate(self, inp: list[str], out: list[str], arg) -> tuple[list, list[str]]:
        """See ``Command.generate``."""
        # Check parameters
        if len(inp) != 1:
            raise ValueError(f"Expecting one input, the LaTeX fls file, got: {inp}")
        path_fls = inp[0]
        if not path_fls.endswith(".fls"):
            raise ValueError(
                f"The input repro_zip_latex command must end with .fls, got {path_fls}."
            )
        if len(out) != 1:
            raise ValueError(f"Expecting one output, the zip file, got: {out}")
        path_zip = out[0]
        if not path_zip.endswith(".zip"):
            raise ValueError(
                f"The output of the repro_zip_latex command must end with .zip, got {path_zip}."
            )
        if arg is not None:
            raise ValueError(f"Expected no arguments, got {arg}")

        # Write builds
        build = {
            "outputs": [path_zip],
            "rule": "zip_latex",
            "inputs": [path_fls],
            "implicit_outputs": [path_fls[:-4] + ".sha256"],
            "pool": "console",
        }
        return [build], []


@attrs.define
class ZipPlain(Command):
    """Create a Reproducible Zip file without checking hashes."""

    @property
    def name(self) -> str:
        """The name of the command in ``reprepbuild.yaml``."""
        return "zip_plain"

    @property
    def rules(self) -> dict[str, dict]:
        """A dict of kwargs for Ninja's ``Writer.rule()``."""
        return {"zip_plain": {"command": "rr-zip-plain ${in} ${out}"}}

    def generate(self, inp: list[str], out: list[str], arg) -> tuple[list, list[str]]:
        """See Command.generate."""
        # Check parameters
        if len(inp) == 0:
            raise ValueError("Expecting at least one input")
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
        path_manifest = get_path_manifest_plain(inp, path_zip)
        exclude = [path_manifest, path_zip]
        inp = [path for path in inp if path not in exclude]
        build = {
            "outputs": [path_zip],
            "rule": "zip_plain",
            "inputs": inp,
            "implicit_outputs": [path_manifest],
            "pool": "console",
        }
        return [build], []


zip_manifest = ZipManifest()
zip_latex = ZipLatex()
zip_plain = ZipPlain()
