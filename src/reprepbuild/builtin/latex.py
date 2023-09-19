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
r"""Compile LaTeX documents with PDFLaTeX.

This module contains code for scanning LaTeX sources for dependencies.
Because LaTeX is a full-blown organically grown programming language,
it is practically impossible to detect all dependencies correctly,
without completely compiling the source.
Because that takes too long and is prone to unexpected errors,
some heuristics are used instead.
Regular expressions are used to detect dependencies with the following commands:

- \input (default extension tex, consistent with PDFLaTeX)
- \import (default extension tex, consistent with PDFLaTeX)
- \includegraphics (our default extension pdf, not png, inconsistent with PDFLaTeX)

There are a few caveats:

- When no image extension is provided, PDFLaTeX tries png before pdf,
  while pdf will allow one to include vector graphics (better quality).
  Hence, when you omit the extension in your source, make sure there is
  not png file, to avoid inconcsistencies with RepRepBuild.
  To avoid any trouble, just add the pdf extension

  See https://tex.stackexchange.com/questions/45498/choosing-whether-to-include-pdf-or-png-in-pdflatex

- Technically, it is possible to use macros and other funny things as
  arguments to the three commands above, in which case RepRepBuild will
  fail to get the dependencies right. Just don't do that.
"""

import os
import re

import attrs

from ..command import Command

__all__ = ("latex", "latex_flat", "latex_diff")


RE_INPUT = re.compile(r"\\input\s*\{(.*?)\}", re.DOTALL)
RE_INCLUDEGRAPHICS = re.compile(r"\\includegraphics(?:\s*\[.*?\])?\s*\{(.*?)\}", re.DOTALL)
RE_BIBLIOGRAPHY = re.compile(r"\\bibliography\s*\{(.*?)\}", re.DOTALL)
RE_IMPORT = re.compile(r"\\import\s*\{(.*?)\}\s*\{(.*?)\}", re.DOTALL)


def cleanup_path(path, ext=None):
    """Clean up a path of a dependency extracted from a LaTeX source.

    Parameters
    ----------
    path
        The path derived from the LaTeX source.
    ext
        The extension to be added

    Returns
    -------
    path_clean
        A cleaned up file name, including the path of the dirname.
    """
    if "." not in os.path.basename(path) and ext is not None:
        path += ext
    path = path.replace("{", "")
    path = path.replace("}", "")
    path = path.strip()
    path = os.path.normpath(path)
    return path


def iter_latex_references(text):
    for fn_inc in re.findall(RE_INPUT, text):
        yield ".", fn_inc, ".tex"
    for fn_inc in re.findall(RE_INCLUDEGRAPHICS, text):
        yield ".", fn_inc, ".pdf"
    for fn_inc in re.findall(RE_BIBLIOGRAPHY, text):
        yield ".", fn_inc, ".bib"
    for new_root, fn_inc in re.findall(RE_IMPORT, text):
        yield new_root, fn_inc, ".tex"


def scan_latex_deps(path_tex, tex_root=None):
    """Scan LaTeX source code for dependencies.

    Parameters
    ----------
    path_tex
        The path to the LaTeX source to scan.
    tex_root
        The directory with respect to which the latex file references should be interpreted.

    Returns
    -------
    implicit
        Filenames to be added to the implicit dependencies.
    not_scanned
        Names of files that should have been scanned, but
        are not present yet.
    bib
        BibTeX files.
    """
    implicit = set()
    not_scanned = set()
    bib = set()

    if os.path.isfile(path_tex):
        if tex_root is None:
            tex_root = os.path.normpath(os.path.dirname(path_tex))
        with open(path_tex) as fh:
            for new_root, fn_inc, ext in iter_latex_references(fh.read()):
                new_root = os.path.normpath(os.path.join(tex_root, new_root))
                path_inc = os.path.normpath(os.path.join(new_root, cleanup_path(fn_inc, ext)))
                if ext == ".bib":
                    bib.add(path_inc)
                else:
                    implicit.add(path_inc)
                if ext == ".tex":
                    sub_implicit, sub_not_scanned, sub_bib = scan_latex_deps(path_inc, new_root)
                    implicit.update(sub_implicit)
                    not_scanned.update(sub_not_scanned)
                    bib.update(sub_bib)
    else:
        # not_scanned is only relevant for missing files,
        # which should be scanned by this function,
        # as soon as they become available.
        not_scanned.add(cleanup_path(path_tex))
    return sorted(implicit), sorted(not_scanned), sorted(bib)


RULES = {
    "bibtex": {
        "command": "cd ${workdir} && "
        "${latex} -recorder -interaction=nonstopmode -draftmode ${stem} > /dev/null && "
        "${bibtex} ${stem}.aux > /dev/null"
    },
    "latex": {
        "command": "cd ${workdir} && export SOURCE_DATE_EPOCH='315532800' && "
        "while [ 1 ]; do ${latex} -recorder ${stem} > /dev/null && "
        "grep 'Rerun to get cross-references right.' ${stem}.log > /dev/null || break; done"
    },
    "latex_diff": {
        "command": "${latexdiff} --append-context2cmd=${latexdiff_context2cmd} ${in} > ${out}"
    },
    "latex_flat": {"command": "rr-latex-flat ${in} ${out}"},
}


@attrs.define
class Latex(Command):
    """Compile LaTeX document sufficient number of times, if needed with BibTeX."""

    @property
    def name(self) -> str:
        """The name of the command in ``reprepbuild.yaml``."""
        return "latex"

    @property
    def rules(self) -> dict[str, dict]:
        """A dict of kwargs for Ninja's ``Writer.rule()``."""
        return RULES

    def generate(self, inp: list[str], out: list[str], arg) -> tuple[list, list[str]]:
        """See Command.generate."""
        # Parse parameters
        if len(inp) != 1:
            raise ValueError(f"Expecting one input file, the main tex file, got: {inp}")
        path_tex = inp[0]
        if not path_tex.endswith(".tex"):
            raise ValueError(f"The input of the latex command must end with .tex, got {path_tex}.")
        prefix = path_tex[:-4]
        workdir, stem = os.path.split(prefix)
        workdir = os.path.normpath(workdir)
        if len(out) != 0:
            raise ValueError(f"Expected no outputs, got: {out}")
        if arg is not None:
            raise ValueError(f"Expected no arguments, got {arg}")

        # Scan Tex file for dependencies.
        implicit, not_scanned, bib = scan_latex_deps(path_tex)

        # Create builds
        builds = []
        if len(bib) > 0:
            builds.append(
                {
                    "rule": "bibtex",
                    "inputs": [path_tex, *bib],
                    "outputs": [f"{prefix}.bbl"],
                    "implicit_outputs": [f"{prefix}.blg"],
                    "implicit": implicit,
                    "variables": {
                        "workdir": workdir,
                        "stem": stem,
                        "latex": "pdflatex",
                        "bibtex": "bibtex",
                    },
                }
            )
            implicit = implicit + bib + [f"{prefix}.bbl"]
        builds.append(
            {
                "rule": "latex",
                "inputs": [path_tex],
                "outputs": [f"{prefix}.pdf"],
                "implicit_outputs": [f"{prefix}.aux", f"{prefix}.log", f"{prefix}.fls"],
                "implicit": implicit,
                "variables": {"workdir": workdir, "stem": stem, "latex": "pdflatex"},
            }
        )

        return builds, not_scanned


class LatexFlat(Command):
    """Flatten a LaTeX file with \\input and/or \\import into a single file."""

    @property
    def name(self) -> str:
        """The name of the command in ``reprepbuild.yaml``."""
        return "latex_flat"

    @property
    def rules(self) -> dict[str, dict]:
        """A dict of kwargs for Ninja's ``Writer.rule()``."""
        return RULES

    def generate(self, inp: list[str], out: list[str], arg) -> tuple[list, list[str]]:
        """See Command.generate."""
        # Parse parameters
        if len(inp) != 1:
            raise ValueError(f"Command latex_flat requires only one inputs, got: {inp}.")
        path_src = inp[0]
        if not path_src.endswith(".tex"):
            raise ValueError(f"The input of the latex command must end with .tex, got {path_src}.")
        if len(out) != 1:
            raise ValueError(f"Expecting one output, the flattened LaTeX file, got: {out}")
        path_flat = out[0]
        if not path_flat.endswith(".tex"):
            raise ValueError(f"The output of latex_flat must end with .tex, got {path_flat}.")
        if arg is not None:
            raise ValueError(f"Expected no arguments, got {arg}")

        # Scan for (missing) dependencies
        implicit, not_scanned, bib = scan_latex_deps(path_src)

        # Create builds
        builds = [
            {
                "outputs": [path_flat],
                "rule": "latex_flat",
                "inputs": [path_src],
                "implicit": implicit,
            }
        ]
        return builds, not_scanned


class LatexDiff(Command):
    """Compile a LaTeX Diff out of two *compiled* source documents."""

    @property
    def name(self) -> str:
        """The name of the command in ``reprepbuild.yaml``."""
        return "latex_diff"

    @property
    def rules(self) -> dict[str, dict]:
        """A dict of kwargs for Ninja's ``Writer.rule()``."""
        return RULES

    def generate(self, inp: list[str], out: list[str], arg) -> tuple[list, list[str]]:
        """See Command.generate."""
        # Argument parsing.
        if len(inp) != 2:
            raise ValueError(f"Command latex_diff requires two inputs, got{inp}.")
        new_tex, old_tex = inp
        if not new_tex.endswith(".tex"):
            raise ValueError(
                f"The inputs of the latex_diff command must end with .tex, got {new_tex}."
            )
        if not old_tex.endswith(".tex"):
            raise ValueError(
                f"The inputs of the latex_diff command must end with .tex, got {old_tex}."
            )
        new_prefix = new_tex[:-4]
        old_prefix = old_tex[:-4]
        if len(out) == 1:
            diff_tex = out[0]
            if not diff_tex.endswith(".tex"):
                raise ValueError(
                    f"The output of the latex_diff must end with .tex, got {diff_tex}."
                )
            diff_prefix = diff_tex[:-4]
        else:
            raise ValueError(f"Command latex_diff requires one output, got {out}.")
        if arg is not None:
            raise ValueError(f"Expected no arguments, got {arg}")

        # Create builds
        latex_diff_variables = {
            "latexdiff_context2cmd": "abstract,supplementary,dataavailability,funding,"
            "authorcontributions,conflictsofinterest,abbreviations",
            "latexdiff": "latexdiff",
        }
        builds = [
            {
                "outputs": [f"{diff_prefix}.bbl"],
                "rule": "latex_diff",
                "inputs": [f"{old_prefix}.bbl", f"{new_prefix}.bbl"],
                "variables": latex_diff_variables,
            },
            {
                "outputs": [f"{diff_prefix}.tex"],
                "rule": "latex_diff",
                "inputs": [f"{old_prefix}.tex", f"{new_prefix}.tex"],
                "variables": latex_diff_variables,
            },
        ]
        return builds, []


latex = Latex()
latex_flat = LatexFlat()
latex_diff = LatexDiff()
