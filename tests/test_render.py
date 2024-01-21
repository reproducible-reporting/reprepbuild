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
"""Unit tests for reprepbuild.scripts.render"""


from reprepbuild.builtin.render import render as render_command
from reprepbuild.scripts.render import render

MAIN_IN_TEX = r"""
\documentclass[a4paper,12pt]{article}
\input{<< public|relpath >>/preamble.inc.tex}
\begin{document}
\end{document}
"""

MAIN_OUT_TEX = r"""
\documentclass[a4paper,12pt]{article}
\input{../preamble.inc.tex}
\begin{document}
\end{document}
"""


def test_relpath():
    variables = {"public": "/home/foo/public"}
    result = render(
        "template.tex", variables, True, str_in=MAIN_IN_TEX, dir_out="/home/foo/public/sub"
    )
    assert result == MAIN_OUT_TEX


BUILDS_RENDER = [
    {
        "rule": "render",
        "inputs": ["sub/foo.md", "sub/bar.json"],
        "outputs": ["/dst/sub/foo.md"],
    },
]


def test_write_build_render():
    builds, _ = render_command.generate(["sub/foo.md", "sub/bar.json"], ["/dst/sub/"], None)
    assert BUILDS_RENDER == builds
