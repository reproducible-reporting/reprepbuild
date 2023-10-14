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

import pytest
from reprepbuild.builtin.latex import latex, latex_diff, latex_flat
from reprepbuild.scripts.latex import (
    DEFAULT_MESSAGE,
    MESSAGE_SUFFIX,
    LatexSourceStack,
    parse_bibtex_log,
    parse_latex_log,
)

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
    builds, gendeps = latex.generate(["sub/main.tex"], [], None, {})
    assert gendeps == ["sub/main.tex"]
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
        builds, gendeps = latex.generate(["main.tex"], [], None, {})
    assert gendeps == ["main.tex", "sub/foo.tex", "table.tex"]
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
        builds, gendeps = latex.generate(["main.tex"], [], None, {})
    assert gendeps == ["main.tex", "sub/foo.tex", "table.tex"]
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
        builds, gendeps = latex.generate(["sub/main.tex"], [], None, {})
    assert gendeps == ["sub/main.tex", "sub/table.tex"]
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
    builds, gendeps = latex_flat.generate(["sub/main.tex"], ["sub/main-flat.tex"], None, {})
    assert gendeps == ["sub/main.tex"]
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
    builds, gendeps = latex_diff.generate(
        ["sub/main.tex", "sub/old/main.tex"], ["sub/main-diff.tex"], None, {}
    )
    assert gendeps == []
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
"""


def test_parse_latex_log1():
    rebuild, error_info = parse_latex_log(io.StringIO(LATEX_LOG1))
    assert not rebuild
    assert error_info.program == "LaTeX"
    assert error_info.src == "./article.tex"
    assert error_info.message.strip() == (LATEX_LOG1_MESSAGE + MESSAGE_SUFFIX).strip()


LATEX_LOG2 = r"""
not so much
"""


def test_parse_latex_log2():
    rebuild, error_info = parse_latex_log(io.StringIO(LATEX_LOG2))
    assert not rebuild
    assert error_info.program == "LaTeX"
    assert error_info.src == "(could not detect source file)"
    assert error_info.message == DEFAULT_MESSAGE


LATEX_LOG3 = r"""
LaTeX Font Info:    Font shape `T1/mdput/m/sl' will be
(Font)              scaled to size 11.28003pt on input line 24.
[1

] (./kwart_cirkelboog_e/divergent.inc.tex

! LaTeX Error: Something's wrong--perhaps a missing \item.

See the LaTeX manual or LaTeX Companion for explanation.
Type  H <return>  for immediate help.
 ...

l.2 \item E
           lektrisch veld opgewekt door continue ladingsverdeling: $\vec{E} ...

Try typing  <return>  to proceed.
If that doesn't work, type  X <return>  to quit.

LaTeX Font Info:    Font shape `OML/mdput/b/n' will be
(Font)              scaled to size 11.28003pt on input line 2.
LaTeX Font Info:    Font shape `OML/mdput/b/n' will be
(Font)              scaled to size 7.52002pt on input line 2.
"""


LATEX_LOG3_MESSAGE = r"""
! LaTeX Error: Something's wrong--perhaps a missing \item.

l.2 \item E
           lektrisch veld opgewekt door continue ladingsverdeling: $\vec{E} ...
"""


def test_parse_latex_log3():
    rebuild, error_info = parse_latex_log(io.StringIO(LATEX_LOG3))
    assert not rebuild
    assert error_info.program == "LaTeX"
    assert error_info.src == "./kwart_cirkelboog_e/divergent.inc.tex"
    assert error_info.message.strip() == (LATEX_LOG3_MESSAGE + MESSAGE_SUFFIX).strip()


LATEX_LOG4 = r"""
**foo
] (./review.tex

(/usr/share/texlive/texmf-dist/tex/latex/mathdesign/mdttfont.def
)

Package hyperref Info: Link coloring ON on input line 29.
(./review.out) (./review.out)
\@outlinefile=\write4
\openout4 = `review.out'.

! Missing $ inserted.
<inserted text>
                $
l.116 \end{gather*}

I've inserted a begin-math/end-math symbol since I think
you left one out. Proceed, with fingers crossed.

LaTeX Font Info:    Font shape `T1/mdput/m/n' will be
(Font)              scaled to size 4.70001pt on input line 116.
! Extra }, or forgotten $.
<template> }
            }\savetaglength@ \endtemplate
l.116 \end{gather*}

I've deleted a group-closing symbol because it seems to be
spurious, as in `$x}$'. But perhaps the } is legitimate and
you forgot something else, as in `\hbox{$x}'. In such cases
the way to recover is to insert both the forgotten and the
deleted material, e.g., by typing `I$}'.

! Extra }, or forgotten $.
<template> }}
             \savetaglength@ \endtemplate
l.116 \end{gather*}

I've deleted a group-closing symbol because it seems to be
spurious, as in `$x}$'. But perhaps the } is legitimate and
you forgot something else, as in `\hbox{$x}'. In such cases
the way to recover is to insert both the forgotten and the
deleted material, e.g., by typing `I$}'.

! Missing $ inserted.
<inserted text>
                $
l.116 \end{gather*}

I've inserted a begin-math/end-math symbol since I think
you left one out. Proceed, with fingers crossed.
"""

LATEX_LOG4_MESSAGE = r"""
! Missing $ inserted.
<inserted text>
                $
l.116 \end{gather*}
"""


def test_parse_latex_log4():
    rebuild, error_info = parse_latex_log(io.StringIO(LATEX_LOG4))
    assert not rebuild
    assert error_info.program == "LaTeX"
    assert error_info.src == "./review.tex"
    assert error_info.message.strip() == (LATEX_LOG4_MESSAGE + MESSAGE_SUFFIX).strip()


LATEX_LOG5 = r"""
This is XeTeX, Version 3.141592653-2.6-0.999994 (TeX Live 2022/CVE-2023-32700 patched)
entering extended mode
 restricted \write18 enabled.
 %&-line parsing enabled.
**solutions
(./solutions.tex
LaTeX2e <2022-06-01> patch level 5
L3 programming layer <2022-12-17> (/usr/share/texlive/texmf-dist/tex/latex/base
/article.cls
Document Class: article 2021/10/04 v1.4n Standard LaTeX document class
(/usr/share/texlive/texmf-dist/tex/latex/base/size12.clo
File: size12.clo 2021/10/04 v1.4n Standard LaTeX file (size option)
)
\bibindent=\dimen140
) (../../../../preamble.inc.tex (/usr/share/texlive/texmf-dist/tex/latex/mathde
sign/mathdesign.sty
))

[1

] (./example/solution.inc.tex
LaTeX Font Info:    Font shape `T1/mdput/m/n' will be
(Font)              scaled to size 7.52002pt on input line 5.
LaTeX Font Info:    Font shape `T1/mdput/m/n' will be
(Font)              scaled to size 4.70001pt on input line 5.
)

! LaTeX Error: Something's wrong--perhaps a missing \item.

See the LaTeX manual or LaTeX Companion for explanation.
Type  H <return>  for immediate help.
 ...

l.40 \end{enumerate}

Try typing  <return>  to proceed.
If that doesn't work, type  X <return>  to quit.
"""

LATEX_LOG5_MESSAGE = r"""
! LaTeX Error: Something's wrong--perhaps a missing \item.

l.40 \end{enumerate}
"""


def test_parse_latex_log5():
    rebuild, error_info = parse_latex_log(io.StringIO(LATEX_LOG5))
    assert not rebuild
    assert error_info.program == "LaTeX"
    assert error_info.src == "./solutions.tex"
    assert error_info.message.strip() == (LATEX_LOG5_MESSAGE + MESSAGE_SUFFIX).strip()


def check_source_stack(latex_log, nline, stack, unfinished):
    lines = latex_log.split("\n")[:nline]
    lss = LatexSourceStack()
    for line in lines:
        lss.feed(line + "\n")
    assert lss.stack == stack
    assert lss.unfinished == unfinished
    assert not lss.unmatched


@pytest.mark.parametrize(
    "nline, stack, unfinished",
    [
        (7, ["./solutions.tex"], None),
        (
            9,
            ["./solutions.tex"],
            "L3 programming layer <2022-12-17> (/usr/share/texlive/texmf-dist/tex/latex/base",
        ),
        (10, ["./solutions.tex", "/usr/share/texlive/texmf-dist/tex/latex/base/article.cls"], None),
        (
            16,
            ["./solutions.tex", "/usr/share/texlive/texmf-dist/tex/latex/base/article.cls"],
            ") (../../../../preamble.inc.tex (/usr/share/texlive/texmf-dist/tex/latex/mathde",
        ),
        (
            17,
            [
                "./solutions.tex",
                "../../../../preamble.inc.tex",
                "/usr/share/texlive/texmf-dist/tex/latex/mathdesign/mathdesign.sty",
            ],
            None,
        ),
        (18, ["./solutions.tex"], None),
        (24, ["./solutions.tex", "./example/solution.inc.tex"], None),
        (30, ["./solutions.tex"], None),
    ],
)
def test_latex_source_stack5(nline, stack, unfinished):
    check_source_stack(LATEX_LOG5, nline, stack, unfinished)


LATEX_LOG6 = r"""
This is XeTeX, Version 3.141592653-2.6-0.999994 (TeX Live 2022/CVE-2023-32700 patched)
entering extended mode
 restricted \write18 enabled.
 %&-line parsing enabled.
**review
(./review.tex

[5] (./weerstand_serie_en_parallel2/method.inc.tex) (./weerstand_serie_en_paral
lel2/answer.inc.tex)
Overfull \hbox (6.20514pt too wide) in paragraph at lines 315--336
\T1/mdput/m/n/12 -  []
 []

(./weerstand_serie_en_parallel2/solution.inc.tex
File: weerstand_serie_en_parallel2//stappen12.pdf Graphic file (type pdf)
<use weerstand_serie_en_parallel2//stappen12.pdf>
[6]
File: weerstand_serie_en_parallel2//stappen34.pdf Graphic file (type pdf)
<use weerstand_serie_en_parallel2//stappen34.pdf>
) (./interactie_eindige_dipolen/stem.inc.tex
File: interactie_eindige_dipolen//paar_dipolen.pdf Graphic file (type pdf)
<use interactie_eindige_dipolen//paar_dipolen.pdf>
) [7] (./interactie_eindige_dipolen/validation.inc.tex)
! Missing $ inserted.
<inserted text>
                $
l.355

I've inserted something that you may have forgotten.
(See the <inserted text> above.)
With luck, this will get me unwedged. But if you
really didn't forget anything, try typing `2' now; then
my insertion and my current dilemma will both disappear.
"""

LATEX_LOG6_MESSAGE = r"""
! Missing $ inserted.
<inserted text>
                $
l.355
"""


def test_parse_latex_log6():
    rebuild, error_info = parse_latex_log(io.StringIO(LATEX_LOG6))
    assert not rebuild
    assert error_info.program == "LaTeX"
    assert error_info.src == "./review.tex"
    assert error_info.message.strip() == (LATEX_LOG6_MESSAGE + MESSAGE_SUFFIX).strip()


LATEX_LOG7 = r"""
(./pdftexcmds.sty
Package: pdftexcmds 2020-06-27 v0.33 Utility functions of pdfTeX for LuaTeX (HO
)
(./infwarerr.sty
Package: infwarerr 2019/12/03 v1.5 Providing info/warning/error messages (HO)
)
)
"""


@pytest.mark.parametrize(
    "nline, stack, unfinished",
    [
        (2, ["./pdftexcmds.sty"], None),
        (
            3,
            ["./pdftexcmds.sty"],
            "Package: pdftexcmds 2020-06-27 v0.33 Utility functions of pdfTeX for LuaTeX (HO",
        ),
        (4, ["./pdftexcmds.sty"], None),
        (5, ["./pdftexcmds.sty", "./infwarerr.sty"], None),
        (6, ["./pdftexcmds.sty", "./infwarerr.sty"], None),
        (7, ["./pdftexcmds.sty"], None),
        (8, [], None),
    ],
)
def test_latex_source_stack7(nline, stack, unfinished):
    check_source_stack(LATEX_LOG7, nline, stack, unfinished)


LATEX_LOG8 = r"""
(/usr/share/texlive/texmf-dist/tex/generic/pgf/basiclayer/pgfcorequick.code.tex
File: pgfcorequick.code.tex 2021/05/15 v3.1.9a (3.1.9a)
)
"""


@pytest.mark.parametrize(
    "nline, stack, unfinished",
    [
        (
            3,
            ["/usr/share/texlive/texmf-dist/tex/generic/pgf/basiclayer/pgfcorequick.code.tex"],
            None,
        ),
    ],
)
def test_latex_source_stack8(nline, stack, unfinished):
    check_source_stack(LATEX_LOG8, nline, stack, unfinished)


LATEX_LOG9 = r"""
(./first.tex
Bluh
(./second.tex))
Blah
"""


@pytest.mark.parametrize(
    "nline, stack, unfinished",
    [
        (2, ["./first.tex"], None),
        (3, ["./first.tex"], None),
        (4, [], None),
        (5, [], None),
    ],
)
def test_latex_source_stack9(nline, stack, unfinished):
    check_source_stack(LATEX_LOG9, nline, stack, unfinished)
