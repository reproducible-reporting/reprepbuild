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
"""Unit tests for reprepbuild.builtin.zip"""


from reprepbuild.builtin.zip import repro_zip, repro_zip_latex

BUILDS_REPRO_ZIP = [
    {
        "rule": "repro_zip",
        "inputs": ["sub/WAWA.sha256"],
        "outputs": ["sub.zip"],
        "pool": "console",
    }
]


def test_write_build_repro_zip():
    builds, _ = repro_zip.generate(["sub/WAWA.sha256"], ["sub.zip"], None, {})
    assert BUILDS_REPRO_ZIP == builds


BUILDS_REPRO_ZIP_LATEX = [
    {
        "rule": "repro_zip_latex",
        "inputs": ["latex-sub/sub.fls"],
        "outputs": ["sub.zip"],
        "pool": "console",
    }
]


def test_write_build_repro_zip_latex():
    builds, _ = repro_zip_latex.generate(["latex-sub/sub.fls"], ["sub.zip"], None, {})
    assert BUILDS_REPRO_ZIP_LATEX == builds
