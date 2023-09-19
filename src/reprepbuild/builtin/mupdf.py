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
"""Transformation of individual files."""

import attrs

from ..command import Command

__all__ = ("pdf_merge", "pdf_add_notes", "pdf_nup")


@attrs.define
class PDFMerge(Command):
    """Merge one or more PDFs into a single file."""

    @property
    def name(self) -> str:
        """The name of the command in ``reprepbuild.yaml``."""
        return "pdf_merge"

    @property
    def rules(self) -> dict[str, dict]:
        """A dict of kwargs for Ninja's ``Writer.rule()``."""
        return {
            "pdf_merge": {"command": "${mutool} merge -o ${out} ${in} && rr-pdf-normalize ${out}"},
        }

    def generate(self, inp: list[str], out: list[str], arg) -> tuple[list, list[str]]:
        """See Command.generate."""
        # Check parameters
        if len(inp) == 0:
            raise ValueError(f"Expecting at least one input PDF, got: {inp}")
        if not all(path_pdf.endswith(".pdf") for path_pdf in inp):
            raise ValueError(f"The input files must end with .pdf, got {inp}.")
        if len(out) != 1:
            raise ValueError(f"Expecting one output, the merged PDF file, got: {out}")
        path_out = out[0]
        if not path_out.endswith(".pdf"):
            raise ValueError(f"The output must end with .pdf, got {path_out}.")
        if arg is not None:
            raise ValueError(f"Expected no arguments, got {arg}")

        # Write builds
        build = {
            "rule": "pdf_merge",
            "outputs": [path_out],
            "inputs": inp,
            "variables": {"mutool": "mutool"},
        }
        return [build], []


@attrs.define
class PDFAddNotes(Command):
    """Insert a notes page at every even page."""

    @property
    def name(self) -> str:
        """The name of the command in ``reprepbuild.yaml``."""
        return "pdf_add_notes"

    @property
    def rules(self) -> dict[str, dict]:
        """A dict of kwargs for Ninja's ``Writer.rule()``."""
        return {
            "pdf_add_notes": {
                "command": "rr-pdf-add-notes ${in} ${out} && rr-pdf-normalize ${out}"
            },
        }

    def generate(self, inp: list[str], out: list[str], arg) -> tuple[list, list[str]]:
        """See Command.generate."""
        # Check parameters
        if len(inp) != 2:
            raise ValueError(f"Expecting two input PDFs, got: {inp}")
        if not all(path_pdf.endswith(".pdf") for path_pdf in inp):
            raise ValueError(f"The input files must end with .pdf, got {inp}.")
        if len(out) != 1:
            raise ValueError(f"Expecting one output PDF file, got: {out}")
        path_out = out[0]
        if not path_out.endswith(".pdf"):
            raise ValueError(f"The output must end with .pdf, got {path_out}.")
        if arg is not None:
            raise ValueError(f"Expected no arguments, got {arg}")

        # Write builds
        build = {
            "rule": "pdf_add_notes",
            "outputs": [path_out],
            "inputs": inp,
        }
        return [build], []


@attrs.define
class PDFNup(Command):
    """Put multiple pages on a single page from PDF source."""

    @property
    def name(self) -> str:
        """The name of the command in ``reprepbuild.yaml``."""
        return "pdf_nup"

    @property
    def rules(self) -> dict[str, dict]:
        """A dict of kwargs for Ninja's ``Writer.rule()``."""
        return {
            "pdf_nup": {
                "command": "rr-pdf-nup ${in} ${nrow} ${ncol} "
                "${margin} ${width} ${height} ${out} && rr-pdf-normalize ${out}"
            },
        }

    def generate(self, inp: list[str], out: list[str], arg) -> tuple[list, list[str]]:
        """See Command.generate."""
        # Check parameters
        if len(inp) != 1:
            raise ValueError(f"Expecting at one input PDF, got: {inp}")
        path_src = inp[0]
        if not path_src.endswith(".pdf"):
            raise ValueError(f"The input file must end with .pdf, got {inp}.")
        if len(out) != 1:
            raise ValueError(f"Expecting one output PDF file, got: {out}")
        path_dst = out[0]
        if not path_dst.endswith(".pdf"):
            raise ValueError(f"The output must end with .pdf, got {path_dst}.")
        if not isinstance(arg, list) and len(arg) == 5:
            raise ValueError("Expecting exactly three arguments")
        arg_types = [int, int, float, float, float]
        for ipar, (par, arg_type) in enumerate(zip(arg, arg_types, strict=True)):
            if not isinstance(par, arg_type):
                raise TypeError(f"Argument item {ipar} should be of type {arg_type}, got: {par}")

        # Write builds
        build = {
            "rule": "pdf_nup",
            "inputs": [path_src],
            "outputs": [path_dst],
            "variables": {
                "nrow": str(arg[0]),
                "ncol": str(arg[1]),
                "margin": f"{arg[2]:.3f}",
                "width": f"{arg[3]:.3f}",
                "height": f"{arg[4]:.3f}",
            },
        }
        return [build], []


pdf_merge = PDFMerge()
pdf_add_notes = PDFAddNotes()
pdf_nup = PDFNup()
