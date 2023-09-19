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
"""Unit tests for reprepbuild.builtin.latex"""

import contextlib
import os

from reprepbuild.builtin.latex import latex, latex_diff, latex_flat

BUILDS_LATEX = [
    {
        "rule": "latex",
        "inputs": ["sub/main.tex"],
        "outputs": ["sub/main.pdf"],
        "implicit_outputs": ["sub/main.aux", "sub/main.log", "sub/main.fls"],
        "implicit": [],
        "variables": {"workdir": "sub", "stem": "main", "latex": "pdflatex"},
    }
]


def test_write_build_latex():
    builds, not_scanned = latex.generate(["sub/main.tex"], [], None)
    assert not_scanned == ["sub/main.tex"]
    assert BUILDS_LATEX == builds


MAIN1_TEX = r"""
\documentclass{article}
\usepackage{graphics}
\usepackage{import}
\begin{document}
\input{table}
\includegraphics{smile}\cite{knuth:1984}
\import{sub}{foo.tex}
\bibliographystyle{unsrt}
\bibliography{references}
\end{document}
"""


BUILDS_LATEX_BIBTEX1 = [
    {
        "rule": "bibtex",
        "inputs": ["main.tex", "references.bib"],
        "outputs": ["main.bbl"],
        "implicit_outputs": ["main.blg"],
        "implicit": ["smile.pdf", "sub/foo.tex", "table.tex"],
        "variables": {"workdir": ".", "stem": "main", "latex": "pdflatex", "bibtex": "bibtex"},
    },
    {
        "rule": "latex",
        "inputs": ["main.tex"],
        "outputs": ["main.pdf"],
        "implicit_outputs": ["main.aux", "main.log", "main.fls"],
        "implicit": ["smile.pdf", "sub/foo.tex", "table.tex", "references.bib", "main.bbl"],
        "variables": {"workdir": ".", "stem": "main", "latex": "pdflatex"},
    },
]


def test_write_build_latex_bibtex1(tmpdir):
    tmpdir = str(tmpdir)
    with open(os.path.join(tmpdir, "main.tex"), "w") as fh:
        fh.write(MAIN1_TEX)
    with contextlib.chdir(tmpdir):
        builds, not_scanned = latex.generate(["main.tex"], [], None)
    assert not_scanned == ["sub/foo.tex", "table.tex"]
    assert BUILDS_LATEX_BIBTEX1 == builds


SUB1_FOO_TEX = r"""
Here is some text.
\includegraphics{plot.pdf}
"""


BUILDS_LATEX_BIBTEX_FOO1 = [
    {
        "rule": "bibtex",
        "inputs": ["main.tex", "references.bib"],
        "outputs": ["main.bbl"],
        "implicit_outputs": ["main.blg"],
        "implicit": ["smile.pdf", "sub/foo.tex", "sub/plot.pdf", "table.tex"],
        "variables": {"workdir": ".", "stem": "main", "latex": "pdflatex", "bibtex": "bibtex"},
    },
    {
        "rule": "latex",
        "inputs": ["main.tex"],
        "outputs": ["main.pdf"],
        "implicit_outputs": ["main.aux", "main.log", "main.fls"],
        "implicit": [
            "smile.pdf",
            "sub/foo.tex",
            "sub/plot.pdf",
            "table.tex",
            "references.bib",
            "main.bbl",
        ],
        "variables": {"workdir": ".", "stem": "main", "latex": "pdflatex"},
    },
]


def test_write_build_latex_bibtex_foo1(tmpdir):
    tmpdir = str(tmpdir)
    with open(os.path.join(tmpdir, "main.tex"), "w") as fh:
        fh.write(MAIN1_TEX)
    subdir = os.path.join(tmpdir, "sub")
    os.mkdir(subdir)
    with open(os.path.join(subdir, "foo.tex"), "w") as fh:
        fh.write(SUB1_FOO_TEX)
    with contextlib.chdir(tmpdir):
        builds, not_scanned = latex.generate(["main.tex"], [], None)
    assert not_scanned == ["table.tex"]
    assert BUILDS_LATEX_BIBTEX_FOO1 == builds


MAIN2_TEX = r"""
\documentclass{article}
\usepackage{graphics}
\usepackage{import}
\begin{document}
\input{table}
\includegraphics{smile}\cite{knuth:1984}
\input{table}
\bibliographystyle{unsrt}
\bibliography{references}
\end{document}
"""

TABLE2_TEX = r"""
Table here.
"""

BUILDS_LATEX_BIBTEX_TABLE2 = [
    {
        "rule": "bibtex",
        "inputs": ["sub/main.tex", "sub/references.bib"],
        "outputs": ["sub/main.bbl"],
        "implicit_outputs": ["sub/main.blg"],
        "implicit": ["sub/smile.pdf", "sub/table.tex"],
        "variables": {"workdir": "sub", "stem": "main", "latex": "pdflatex", "bibtex": "bibtex"},
    },
    {
        "rule": "latex",
        "inputs": ["sub/main.tex"],
        "outputs": ["sub/main.pdf"],
        "implicit_outputs": ["sub/main.aux", "sub/main.log", "sub/main.fls"],
        "implicit": ["sub/smile.pdf", "sub/table.tex", "sub/references.bib", "sub/main.bbl"],
        "variables": {"workdir": "sub", "stem": "main", "latex": "pdflatex"},
    },
]


def test_write_build_latex_bibtex_table2(tmpdir):
    tmpdir = str(tmpdir)
    subdir = os.path.join(tmpdir, "sub")
    os.mkdir(subdir)
    with open(os.path.join(subdir, "main.tex"), "w") as fh:
        fh.write(MAIN2_TEX)
    with open(os.path.join(subdir, "table.tex"), "w") as fh:
        fh.write(TABLE2_TEX)
    with contextlib.chdir(tmpdir):
        builds, not_scanned = latex.generate(["sub/main.tex"], [], None)
    assert not_scanned == []
    assert BUILDS_LATEX_BIBTEX_TABLE2 == builds


BUILDS_LATEX_FLAT = [
    {
        "implicit": [],
        "inputs": ["sub/main.tex"],
        "outputs": ["sub/main-flat.tex"],
        "rule": "latex_flat",
    }
]


def test_write_build_latex_flat():
    builds, not_scanned = latex_flat.generate(["sub/main.tex"], ["sub/main-flat.tex"], None)
    assert not_scanned == ["sub/main.tex"]
    assert BUILDS_LATEX_FLAT == builds


BUILDS_LATEX_DIFF = [
    {
        "inputs": ["sub/old/main.bbl", "sub/main.bbl"],
        "outputs": ["sub/main-diff.bbl"],
        "rule": "latex_diff",
        "variables": {
            "latexdiff": "latexdiff",
            "latexdiff_context2cmd": "abstract,supplementary,dataavailability,funding,"
            "authorcontributions,conflictsofinterest,abbreviations",
        },
    },
    {
        "inputs": ["sub/old/main.tex", "sub/main.tex"],
        "outputs": ["sub/main-diff.tex"],
        "rule": "latex_diff",
        "variables": {
            "latexdiff": "latexdiff",
            "latexdiff_context2cmd": "abstract,supplementary,dataavailability,funding,"
            "authorcontributions,conflictsofinterest,abbreviations",
        },
    },
]


def test_write_build_latex_diff():
    builds, not_scanned = latex_diff.generate(
        ["sub/main.tex", "sub/old/main.tex"], ["sub/main-diff.tex"], None
    )
    assert not_scanned == []
    assert BUILDS_LATEX_DIFF == builds
