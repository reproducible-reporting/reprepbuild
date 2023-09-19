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
"""Unit tests for reprepbuild.builtin.python_script"""

import contextlib
import os

from reprepbuild.builtin.python_script import python_script

SCRIPT = """
def reprepbuild_info():
    return {
        "outputs": ["result.txt"],
    }


def main(outputs):
    pass
"""


BUILDS_PYTHON_SCRIPT = [
    {
        "implicit": [],
        "implicit_outputs": ["result.txt"],
        "inputs": ["foo.py"],
        "outputs": [".foo.log"],
        "rule": "python_script",
        "variables": {"argstr": "foo", "out_prefix": ".foo"},
    }
]


def test_write_build_python_script(tmpdir):
    tmpdir = str(tmpdir)
    with open(os.path.join(tmpdir, "foo.py"), "w") as fh:
        fh.write(SCRIPT)
    with contextlib.chdir(tmpdir):
        builds, _ = python_script.generate(["foo.py"], [], None)
    assert BUILDS_PYTHON_SCRIPT == builds


BUILDS_PYTHON_SCRIPT_SUB = [
    {
        "implicit": [],
        "implicit_outputs": ["sub/result.txt"],
        "inputs": ["sub/foo.py"],
        "outputs": ["sub/.foo.log"],
        "rule": "python_script",
        "variables": {"argstr": "foo", "out_prefix": "sub/.foo"},
    }
]


def test_write_build_python_script_sub(tmpdir):
    tmpdir = str(tmpdir)
    subdir = os.path.join(tmpdir, "sub")
    os.mkdir(subdir)
    with open(os.path.join(subdir, "foo.py"), "w") as fh:
        fh.write(SCRIPT)
    with contextlib.chdir(tmpdir):
        builds, _ = python_script.generate(["sub/foo.py"], [], None)
    assert BUILDS_PYTHON_SCRIPT_SUB == builds
