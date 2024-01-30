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
"""Unit tests for reprepbuild.config"""

import contextlib
import os

from reprepbuild.builtin.transform import copy
from reprepbuild.config import LoopConfig, iterate_loop_config, load_config
from reprepbuild.generator import BuildGenerator

CONSTANTS_JSON = """\
{
  "foo": "bar",
  "spam": "egg-${foo}",
  "public": "${root}/${spam}/bacon",
  "inkscape": "/home/spammer/bin/inkscape"
}"""

TEST_CONFIG = """\
imports:
- reprepbuild.builtin
tasks:
- subdir: sub1
- command: copy
  inp: egg
  out: ${public}/
- subdir: sub2
"""

TEST_SUB1_CONFIG = """\
imports:
- reprepbuild.builtin
tasks:
- command: copy
  inp: one-foo${*id}.txt
  out: ${public}/${here}/${var1}${*id}.txt
  override:
    spam: yum
    var1: usr
"""

TEST_SUB2_CONFIG = """\
imports:
- reprepbuild.builtin
tasks:
- command: copy
  inp: some-${foo}*.txt
  out: ${public}/${here}/bin
  default: false
"""

CREATE_FILES = {
    "constants.json": CONSTANTS_JSON,
    "reprepbuild.yaml": TEST_CONFIG,
    "sub1/reprepbuild.yaml": TEST_SUB1_CONFIG,
    "sub2/reprepbuild.yaml": TEST_SUB2_CONFIG,
    "egg": "",
    "sub1/one-foo1": "",
    "sub1/one-foo2": "",
    "sub2/some-bar3.txt": "",
    "sub2/some-bar4.txt": "",
}


def test_config_example(tmpdir: str):
    tmpdir = str(tmpdir)
    for filename, contents in CREATE_FILES.items():
        path_dst = os.path.join(tmpdir, filename)
        os.makedirs(os.path.dirname(path_dst), exist_ok=True)
        with open(path_dst, "w") as fh:
            fh.write(contents)
    tasks = []
    with contextlib.chdir(tmpdir):
        load_config(tmpdir, os.path.join(tmpdir, "reprepbuild.yaml"), ["constants.json"], tasks)

    constants = {
        "inkscape": "/home/spammer/bin/inkscape",
        "foo": "bar",
        "spam": "egg-bar",
        "public": os.path.join(tmpdir, "egg-bar", "bacon"),
        "root": tmpdir,
        "here": ".",
    }

    assert len(tasks) == 3
    assert tasks[0] == BuildGenerator(
        copy,
        ["sub1/one-foo${*id}.txt"],
        ["egg-bar/bacon/sub1/usr${*id}.txt"],
        constants | {"here": "sub1", "spam": "yum", "var1": "usr"},
    )
    assert tasks[1] == BuildGenerator(copy, ["egg"], ["egg-bar/bacon/"], constants)
    assert tasks[2] == BuildGenerator(
        copy,
        ["sub2/some-bar*.txt"],
        ["egg-bar/bacon/sub2/bin"],
        constants | {"here": "sub2"},
        default=False,
    )


def test_iterate_loop_config():
    loop1 = LoopConfig("food", "egg spam")
    assert loop1.key == ["food"]
    assert loop1.val == [["egg"], ["spam"]]
    assert list(iterate_loop_config([loop1])) == [
        {"food": "egg"},
        {"food": "spam"},
    ]

    loop2 = LoopConfig("time place", ["now here", "tomorrow home", "never there"])
    assert loop2.key == ["time", "place"]
    assert loop2.val == [["now", "here"], ["tomorrow", "home"], ["never", "there"]]
    assert list(iterate_loop_config([loop2])) == [
        {"time": "now", "place": "here"},
        {"time": "tomorrow", "place": "home"},
        {"time": "never", "place": "there"},
    ]

    assert list(iterate_loop_config([loop1, loop2])) == [
        {"food": "egg", "time": "now", "place": "here"},
        {"food": "egg", "time": "tomorrow", "place": "home"},
        {"food": "egg", "time": "never", "place": "there"},
        {"food": "spam", "time": "now", "place": "here"},
        {"food": "spam", "time": "tomorrow", "place": "home"},
        {"food": "spam", "time": "never", "place": "there"},
    ]


TEST_LOOP_CONFIG = """\
imports:
- reprepbuild.builtin
tasks:
- command: copy
  loop:
    - key: [foo, bar]
      val: [[one, two], [aa, bbbb]]
  inp: some-${foo}.txt
  out: other-${bar}.txt
"""


def test_loop_config(tmpdir: str):
    tmpdir = str(tmpdir)
    with open(os.path.join(tmpdir, "reprepbuild.yaml"), "w") as fh:
        fh.write(TEST_LOOP_CONFIG)
    tasks = []
    with contextlib.chdir(tmpdir):
        load_config(tmpdir, os.path.join(tmpdir, "reprepbuild.yaml"), [], tasks)
    assert len(tasks) == 2
    assert tasks[0] == BuildGenerator(
        copy,
        ["some-one.txt"],
        ["other-two.txt"],
        {"here": ".", "root": tmpdir, "foo": "one", "bar": "two"},
    )
    assert tasks[1] == BuildGenerator(
        copy,
        ["some-aa.txt"],
        ["other-bbbb.txt"],
        {"here": ".", "root": tmpdir, "foo": "aa", "bar": "bbbb"},
    )
