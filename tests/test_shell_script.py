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
"""Unit tests for reprepbuild.builtin.shell_script"""

import contextlib
import os

from reprepbuild.builtin.shell_script import shell_script

SCRIPT = """
#!/usr/bin/env somesh

#REPREPBUILD inputs foo.txt milk.csv
#REPREPBUILD inputs egg.txt
#REPREPBUILD outputs spam.txt
#REPREPBUILD outputs bar.txt
"""


BUILDS_PYTHON_SCRIPT = [
    {
        "implicit": ["foo.txt", "milk.csv", "egg.txt"],
        "implicit_outputs": ["spam.txt", "bar.txt"],
        "inputs": ["script.sh"],
        "outputs": [".script.log"],
        "rule": "shell_script",
    },
]


def test_write_build_shell_script(tmpdir):
    tmpdir = str(tmpdir)
    with open(os.path.join(tmpdir, "script.sh"), "w") as fh:
        fh.write(SCRIPT)
    with contextlib.chdir(tmpdir):
        builds, ns = shell_script.generate(["script.sh"], [], None)
    assert BUILDS_PYTHON_SCRIPT == builds
    assert ns == ["script.sh"]
