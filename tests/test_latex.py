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
"""Unit tests for reprepbuild.builtin.latex and reprepbuild.scripts.latex"""

import contextlib
import io
import os

from reprepbuild.builtin.latex import latex, latex_diff, latex_flat
from reprepbuild.scripts.latex import DEFAULT_MESSAGE, parse_bibtex_log, parse_latex_log

BUILDS_LATEX = [
    {
        "rule": "latex",
        "inputs": ["sub/main.tex"],
        "outputs": ["sub/main.pdf"],
        "implicit_outputs": ["sub/main.log", "sub/main.aux", "sub/main.out", "sub/main.fls"],
        "implicit": [],
        "variables": {"latex": "pdflatex"},
    }
]


def test_write_build_latex():
    builds, not_scanned = latex.generate(["sub/main.tex"], [], None, {})
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
        "rule": "latex_bibtex",
        "inputs": ["main.tex"],
        "outputs": ["main.pdf"],
        "implicit_outputs": [
            "main.blg",
            "main.bbl",
            "main.log",
            "main.aux",
            "main.out",
            "main.fls",
        ],
        "implicit": ["smile.pdf", "sub/foo.tex", "table.tex", "references.bib"],
        "variables": {
            "latex": "pdflatex",
            "bibtex": "bibtex",
            "bibsane": "bibsane",
            "bibsane_config": "${root}/bibsane.yaml",
        },
    }
]


def test_write_build_latex_bibtex1(tmpdir):
    tmpdir = str(tmpdir)
    with open(os.path.join(tmpdir, "main.tex"), "w") as fh:
        fh.write(MAIN1_TEX)
    with contextlib.chdir(tmpdir):
        builds, not_scanned = latex.generate(["main.tex"], [], None, {})
    assert not_scanned == ["sub/foo.tex", "table.tex"]
    assert BUILDS_LATEX_BIBTEX1 == builds


SUB1_FOO_TEX = r"""
Here is some text.
\includegraphics{plot.pdf}
"""


BUILDS_LATEX_BIBTEX_FOO1 = [
    {
        "rule": "latex_bibtex",
        "inputs": ["main.tex"],
        "outputs": ["main.pdf"],
        "implicit_outputs": [
            "main.blg",
            "main.bbl",
            "main.log",
            "main.aux",
            "main.out",
            "main.fls",
        ],
        "implicit": ["smile.pdf", "sub/foo.tex", "sub/plot.pdf", "table.tex", "references.bib"],
        "variables": {
            "latex": "pdflatex",
            "bibtex": "bibtex",
            "bibsane": "bibsane",
            "bibsane_config": "${root}/bibsane.yaml",
        },
    }
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
        builds, not_scanned = latex.generate(["main.tex"], [], None, {})
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
        "rule": "latex_bibtex",
        "inputs": ["sub/main.tex"],
        "outputs": ["sub/main.pdf"],
        "implicit_outputs": [
            "sub/main.blg",
            "sub/main.bbl",
            "sub/main.log",
            "sub/main.aux",
            "sub/main.out",
            "sub/main.fls",
        ],
        "implicit": ["sub/smile.pdf", "sub/table.tex", "sub/references.bib"],
        "variables": {
            "latex": "pdflatex",
            "bibtex": "bibtex",
            "bibsane": "bibsane",
            "bibsane_config": "${root}/bibsane.yaml",
        },
    }
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
        builds, not_scanned = latex.generate(["sub/main.tex"], [], None, {})
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
    builds, not_scanned = latex_flat.generate(["sub/main.tex"], ["sub/main-flat.tex"], None, {})
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
        ["sub/main.tex", "sub/old/main.tex"], ["sub/main-diff.tex"], None, {}
    )
    assert not_scanned == []
    assert BUILDS_LATEX_DIFF == builds


BIBTEX_BLG1 = """\
This is BibTeX, Version 0.99d (TeX Live 2022/CVE-2023-32700 patched)
Capacity: max_strings=200000, hash_size=200000, hash_prime=170003
The top-level auxiliary file: article.aux
The style file: achemso.bst
Reallocated singl_function (elt_size=4) to 100 items from 50.
Database file #1: acs-article.bib
Database file #2: references.bib
I was expecting a `{' or a `('---line 12 of file references.bib
 :
 : @article{SomeAuthor1999,
(Error may have been on previous line)
I'm skipping whatever remains of this entry
achemso 2022-11-25 v3.13f
You've used 62 entries,
            2538 wiz_defined-function locations,
            1232 strings with 23159 characters,
and the built_in function-call counts, 27532 in all, are:
"""

BIBTEX_BLG1_MESSAGE = """\
I was expecting a `{' or a `('---line 12 of file references.bib
 :
 : @article{SomeAuthor1999,
(Error may have been on previous line)
I'm skipping whatever remains of this entry
"""


def test_parse_bibtex_log1():
    error_info = parse_bibtex_log(io.StringIO(BIBTEX_BLG1))
    assert error_info.program == "BibTeX"
    assert error_info.src == "references.bib"
    assert error_info.message == BIBTEX_BLG1_MESSAGE.strip()


LATEX_LOG1 = r"""
**article
(./article.tex
LaTeX2e <2022-06-01> patch level 5

[17] [18] [19]
<fig1.pdf, id=90, 200pt x 200pt>
File: fig1.pdf Graphic file (type pdf)
<use fig1.pdf>
Package pdftex.def Info: fig1.pdf  used on input line 300.
(pdftex.def)             Requested size:  200pt x 200pt.
[20] [21]
! Undefined control sequence.
l.396         \begin{center}\foo

The control sequence at the end of the top line
of your error message was never \def'ed. If you have
misspelled it (e.g., `\hobx'), type `I' and the correct
spelling (e.g., `I\hbox'). Otherwise just continue,
and I'll forget about whatever was undefined.

<fig2.pdf, id=97, 100pt x 100pt>
File: fig2.pdf Graphic file (type pdf)
<use fig2.pdf>
"""

LATEX_LOG1_MESSAGE = r"""
! Undefined control sequence.
l.396         \begin{center}\foo

The control sequence at the end of the top line
of your error message was never \def'ed. If you have
misspelled it (e.g., `\hobx'), type `I' and the correct
spelling (e.g., `I\hbox'). Otherwise just continue,
and I'll forget about whatever was undefined.
"""


def test_parse_latex_log1():
    rebuild, error_info = parse_latex_log(io.StringIO(LATEX_LOG1))
    assert not rebuild
    assert error_info.program == "LaTeX"
    assert error_info.src == "./article.tex"
    assert error_info.message.strip() == LATEX_LOG1_MESSAGE.strip()


LATEX_LOG2 = r"""
not so much
"""


def test_parse_latex_log2():
    rebuild, error_info = parse_latex_log(io.StringIO(LATEX_LOG2))
    assert not rebuild
    assert error_info.program == "LaTeX"
    assert error_info.src == "(could not detect source file)"
    assert error_info.message == DEFAULT_MESSAGE
