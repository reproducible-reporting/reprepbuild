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
"""Unit tests for reprepbuild.scripts.latex_flat"""


import os

from reprepbuild.scripts.latex_flat import flatten_latex

MAIN_TEX = r"""
\begin{document}
\input{table}
\includegraphics{smile}\cite{knuth:1984}
\import{sub}{foo.tex}
\end{document}
"""

TABLE_TEX = "This is a table.\n"

FOO_TEX = r"""This is a foo.
\includegraphics[width=5cm]{smile.pdf}
\thebibliography{references}
\input{other.tex}
"""

OTHER_TEX = "Another line.\n"

EXPECTED = r"""
\begin{document}
This is a table.
\includegraphics{../smile}\cite{knuth:1984}
This is a foo.
\includegraphics[width=5cm]{../sub/smile.pdf}
\thebibliography{../sub/references}
Another line.
\end{document}
"""

CREATE_FILES = {
    "main.tex": MAIN_TEX,
    "table.tex": TABLE_TEX,
    "sub/foo.tex": FOO_TEX,
    "sub/other.tex": OTHER_TEX,
}


def test_latex_flat(tmpdir):
    tmpdir = str(tmpdir)
    for filename, contents in CREATE_FILES.items():
        path_dst = os.path.join(tmpdir, filename)
        os.makedirs(os.path.dirname(path_dst), exist_ok=True)
        with open(path_dst, "w") as fh:
            fh.write(contents)
    flatdir = os.path.join(tmpdir, "flat")
    os.mkdir(flatdir)
    with open(os.path.join(flatdir, "main.tex"), "w") as fh:
        flatten_latex(os.path.join(tmpdir, "main.tex"), fh, flatdir)
    with open(os.path.join(flatdir, "main.tex")) as fh:
        result = fh.read()
    assert result.strip() == EXPECTED.strip()
