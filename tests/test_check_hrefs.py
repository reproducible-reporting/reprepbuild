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
"""Unit tests for reprepbuild.builtin.check_hrefs"""


from reprepbuild.builtin.check_hrefs import check_hrefs

BUILDS_CHECK_HREFS = [
    {
        "rule": "check_hrefs",
        "inputs": ["sub/boo.md"],
        "outputs": ["sub/.boo.md-check_hrefs.log"],
        "variables": {"cli_args": ""},
    },
    {
        "rule": "check_hrefs",
        "inputs": ["foo/plop.pdf"],
        "outputs": ["foo/.plop.pdf-check_hrefs.log"],
        "variables": {"cli_args": ""},
    },
]


def test_write_build_check_hrefs():
    builds, _ = check_hrefs.generate(["sub/boo.md", "foo/plop.pdf"], [], None)
    assert BUILDS_CHECK_HREFS == builds


BUILDS_CHECK_HREFS_TRANSLATE = [
    {
        "rule": "check_hrefs",
        "inputs": ["sub/boo.md"],
        "outputs": ["sub/.boo.md-check_hrefs.log"],
        "variables": {"cli_args": "--translate foo bar egg spam"},
    },
]


def test_write_build_check_hrefs_translate():
    arg = {"translate": [["foo", "bar"], ["egg", "spam"]]}
    builds, _ = check_hrefs.generate(["sub/boo.md"], [], arg)
    assert BUILDS_CHECK_HREFS_TRANSLATE == builds


BUILDS_CHECK_HREFS_IGNORE = [
    {
        "rule": "check_hrefs",
        "inputs": ["sub/boo.md"],
        "outputs": ["sub/.boo.md-check_hrefs.log"],
        "variables": {"cli_args": "--ignore foo bar egg"},
    },
]


def test_write_build_check_hrefs_ignore():
    arg = {"ignore": ["foo", "bar", "egg"]}
    builds, _ = check_hrefs.generate(["sub/boo.md"], [], arg)
    assert BUILDS_CHECK_HREFS_IGNORE == builds
