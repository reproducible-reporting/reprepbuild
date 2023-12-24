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
"""Unit tests for reprepbuild.generator"""

import contextlib
import os

import pytest
from reprepbuild.builtin import convert_svg_pdf, copy, latex, python_script
from reprepbuild.generator import BarrierGenerator, BuildGenerator, _clean_build, _split_if_string


def test_split_if_string():
    assert _split_if_string("aaa bbb c   ddd\nee") == ["aaa", "bbb", "c", "ddd", "ee"]
    assert _split_if_string(["45", "23453", "23"]) == ["45", "23453", "23"]


def test_clean_build():
    for key in "inputs", "outputs", "implicit", "order_only", "implicit_outputs", "variables":
        build = {key: []}
        _clean_build(build)
        assert key not in build
    for key in "implicit", "order_only", "implicit_outputs":
        build = {key: ["aaa", "bbb", "aaa"]}
        _clean_build(build)
        assert build[key] == ["aaa", "bbb"]


def test_generate_named_wildcard_inp_out(tmpdir):
    tmpdir = str(tmpdir)
    gen = BuildGenerator(copy, True, {}, ["foo${*id}.txt"], ["bar${*id}.txt"])
    previous_outputs = {"foo1.txt", "foo3.txt"}
    with contextlib.chdir(tmpdir):
        results = list(gen(previous_outputs, set()))
    [records0, ns0], [records1, ns1] = results
    assert records0 == [
        "command: copy",
        "inp: foo1.txt",
        "out: bar1.txt",
        {"rule": "copy", "outputs": ["bar1.txt"], "inputs": ["foo1.txt"]},
        ["bar1.txt"],
    ]
    assert ns0 == []
    assert records1 == [
        "command: copy",
        "inp: foo3.txt",
        "out: bar3.txt",
        {"rule": "copy", "outputs": ["bar3.txt"], "inputs": ["foo3.txt"]},
        ["bar3.txt"],
    ]
    assert ns1 == []


def test_generate_anonymous_wildcard_inp_out(tmpdir):
    tmpdir = str(tmpdir)
    gen = BuildGenerator(copy, True, {}, ["foo*.txt"], ["bar/"])
    previous_outputs = {"foo1.txt", "foo3.txt"}
    with contextlib.chdir(tmpdir):
        results = list(gen(previous_outputs, set()))
    [[records, ns]] = results
    assert records == [
        "command: copy",
        "inp: foo1.txt foo3.txt",
        "out: bar/",
        {
            "rule": "copy_mkdir",
            "outputs": ["bar/foo1.txt"],
            "inputs": ["foo1.txt"],
            "variables": {"dstdirs": "bar"},
        },
        ["bar/foo1.txt"],
        {
            "rule": "copy_mkdir",
            "outputs": ["bar/foo3.txt"],
            "inputs": ["foo3.txt"],
            "variables": {"dstdirs": "bar"},
        },
        ["bar/foo3.txt"],
    ]
    assert ns == []


def test_generate_named_wildcard_inp_inp_out(tmpdir):
    tmpdir = str(tmpdir)
    gen = BuildGenerator(copy, True, {}, ["foo${*id}.txt", "bar${*id}.txt"], ["spam${*id}/"])
    previous_outputs = {"foo1.txt", "bar2.txt", "foo3.txt", "bar3.txt"}
    with contextlib.chdir(tmpdir):
        results = list(gen(previous_outputs, set()))
    [[records, ns]] = results
    assert records == [
        "command: copy",
        "inp: foo3.txt bar3.txt",
        "out: spam3/",
        {
            "rule": "copy_mkdir",
            "outputs": ["spam3/foo3.txt"],
            "inputs": ["foo3.txt"],
            "variables": {"dstdirs": "spam3"},
        },
        ["spam3/foo3.txt"],
        {
            "rule": "copy_mkdir",
            "outputs": ["spam3/bar3.txt"],
            "inputs": ["bar3.txt"],
            "variables": {"dstdirs": "spam3"},
        },
        ["spam3/bar3.txt"],
    ]
    assert ns == []


PYTHON_SCRIPT = """
def reprepbuild_info():
    return {
        "inputs": ["foo.txt"],
        "outputs": ["bar.txt"],
    }

def main(inputs, outputs):
    pass
"""


@pytest.mark.parametrize("ignore", [True, False])
def test_generate_ignore_missing(tmpdir, ignore):
    tmpdir = str(tmpdir)
    with open(os.path.join(tmpdir, "script.py"), "w") as fh:
        fh.write(PYTHON_SCRIPT)
    variables = {"ignore_missing": "foo*"} if ignore else {}
    gen = BuildGenerator(python_script, True, variables, ["script.py"], [])
    previous_outputs = {}
    with contextlib.chdir(tmpdir):
        results = list(gen(previous_outputs, set()))
    [[records, ns]] = results
    if ignore:
        print(records)
        assert records == [
            "command: python_script",
            "inp: script.py",
            {
                "outputs": [".script.log"],
                "rule": "error",
                "variables": {"message": "Missing inputs: foo.txt"},
            },
            {"inputs": [".script.log"], "rule": "phony", "outputs": ["script"]},
        ]

    else:
        assert records == [
            "command: python_script",
            "inp: script.py",
            {
                "inputs": ["script.py"],
                "implicit": ["foo.txt"],
                "rule": "python_script",
                "implicit_outputs": ["bar.txt"],
                "outputs": [".script.log"],
                "variables": {"argstr": "script", "out_prefix": ".script"},
            },
            [".script.log"],
            {"inputs": [".script.log"], "outputs": ["script"], "rule": "phony"},
        ]
    assert ns == ["script.py"]


def test_generate_variables(tmpdir):
    tmpdir = str(tmpdir)
    gen = BuildGenerator(
        convert_svg_pdf,
        True,
        {"inkscape": "my-special-inkscape"},
        ["template/logo.svg"],
        ["public/logo.pdf"],
    )
    previous_outputs = {"template/logo.svg"}
    with contextlib.chdir(tmpdir):
        results = list(gen(previous_outputs, set()))
    [[records, ns]] = results
    assert records == [
        "command: convert_svg_pdf",
        "inp: template/logo.svg",
        "out: public/logo.pdf",
        {
            "rule": "convert_svg_pdf_mkdir",
            "outputs": ["public/logo.pdf"],
            "pool": "convert_svg_pdf",
            "inputs": ["template/logo.svg"],
            "variables": {"dstdirs": "public", "inkscape": "my-special-inkscape"},
        },
        ["public/logo.pdf"],
    ]
    assert ns == []


def test_generate_no_defaults(tmpdir):
    tmpdir = str(tmpdir)
    gen = BuildGenerator(copy, False, {}, ["README.md"], ["public/README.md"])
    previous_outputs = {"README.md"}
    with contextlib.chdir(tmpdir):
        results = list(gen(previous_outputs, set()))
    [[records, ns]] = results
    assert records == [
        "command: copy",
        "inp: README.md",
        "out: public/README.md",
        {
            "rule": "copy_mkdir",
            "outputs": ["public/README.md"],
            "inputs": ["README.md"],
            "variables": {"dstdirs": "public"},
        },
    ]
    assert ns == []


MAIN_TEX = r"""
\documentclass{article}
\begin{document}
\input{table}
\end{document}
"""


def test_generate_not_scanned(tmpdir):
    tmpdir = str(tmpdir)
    with open(os.path.join(tmpdir, "main.tex"), "w") as fh:
        fh.write(MAIN_TEX)
    gen = BuildGenerator(latex, False, {}, ["main.tex"], [])
    previous_outputs = {}
    with contextlib.chdir(tmpdir):
        results = list(gen(previous_outputs, set()))
    [[records, gd]] = results
    assert records == [
        "command: latex",
        "inp: main.tex",
        {
            "rule": "latex",
            "inputs": ["main.tex"],
            "outputs": ["main.pdf"],
            "implicit_outputs": ["main.aux", "main.fls", "main.log"],
            "implicit": ["table.tex"],
            "variables": {"latex": "pdflatex"},
        },
    ]
    assert gd == ["main.tex", "table.tex"]


def test_generate_barrier(tmpdir):
    tmpdir = str(tmpdir)
    gen = BarrierGenerator("hold")
    previous_outputs = {"foo.txt", "bar.txt", "ignored.txt"}
    defaults = {"foo.txt", "bar.txt"}
    with contextlib.chdir(tmpdir):
        results = list(gen(previous_outputs, defaults))
    [[records, ns]] = results
    assert records == [{"inputs": ["bar.txt", "foo.txt"], "outputs": ["hold"], "rule": "phony"}]
    assert ns == []
