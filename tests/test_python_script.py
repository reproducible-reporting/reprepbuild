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
    },
    {"inputs": [".foo.log"], "outputs": ["foo"], "rule": "phony"},
]


def test_write_build_python_script(tmpdir):
    tmpdir = str(tmpdir)
    with open(os.path.join(tmpdir, "foo.py"), "w") as fh:
        fh.write(SCRIPT)
    with contextlib.chdir(tmpdir):
        builds, ns = python_script.generate(["foo.py"], [], None)
    assert BUILDS_PYTHON_SCRIPT == builds
    assert ns == ["foo.py"]


BUILDS_PYTHON_SCRIPT_SUB = [
    {
        "implicit": [],
        "implicit_outputs": ["sub/result.txt"],
        "inputs": ["sub/foo.py"],
        "outputs": ["sub/.foo.log"],
        "rule": "python_script",
        "variables": {"argstr": "foo", "out_prefix": "sub/.foo"},
    },
    {"inputs": ["sub/.foo.log"], "outputs": ["sub/foo"], "rule": "phony"},
]


def test_write_build_python_script_sub(tmpdir):
    tmpdir = str(tmpdir)
    subdir = os.path.join(tmpdir, "sub")
    os.mkdir(subdir)
    with open(os.path.join(subdir, "foo.py"), "w") as fh:
        fh.write(SCRIPT)
    with contextlib.chdir(tmpdir):
        builds, ns = python_script.generate(["sub/foo.py"], [], None)
    assert BUILDS_PYTHON_SCRIPT_SUB == builds
    assert ns == ["sub/foo.py"]


BUILDS_PYTHON_SCRIPT_CONSTANTS = [
    {
        "implicit": ["constants.json"],
        "implicit_outputs": ["result.txt"],
        "inputs": ["foo.py"],
        "outputs": [".foo.log"],
        "rule": "python_script",
        "variables": {"argstr": "foo", "out_prefix": ".foo", "script_opts": "-c constants.json"},
    },
    {"inputs": [".foo.log"], "outputs": ["foo"], "rule": "phony"},
]


CONSTANTS_JSON = '{"name": "value"}'


def test_write_build_python_script_constants(tmpdir):
    tmpdir = str(tmpdir)
    with open(os.path.join(tmpdir, "foo.py"), "w") as fh:
        fh.write(SCRIPT)
    with open(os.path.join(tmpdir, "constants.json"), "w") as fh:
        fh.write(CONSTANTS_JSON)
    with contextlib.chdir(tmpdir):
        builds, ns = python_script.generate(["foo.py", "constants.json"], [], None)
    assert BUILDS_PYTHON_SCRIPT_CONSTANTS == builds
    assert ns == ["foo.py", "constants.json"]
