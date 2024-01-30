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
    gen = BuildGenerator(copy, ["foo${*id}.txt"], ["bar${*id}.txt"])
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


def test_generate_named_wildcard2_inp_out(tmpdir):
    tmpdir = str(tmpdir)
    gen = BuildGenerator(copy, ["foo${*id1}.txt", "bar${*id2}.txt"], ["f${*id1}/b${*id2}/"])
    previous_outputs = {"foo1.txt", "foo2.txt", "bar3.txt", "bar4.txt"}
    with contextlib.chdir(tmpdir):
        results = list(gen(previous_outputs, set()))
    for i in 1, 2:
        for j in 3, 4:
            records, ns = results.pop(0)
            assert records == [
                "command: copy",
                f"inp: foo{i}.txt bar{j}.txt",
                f"out: f{i}/b{j}/",
                {
                    "rule": "copy",
                    "inputs": [f"foo{i}.txt"],
                    "outputs": [f"f{i}/b{j}/foo{i}.txt"],
                    "variables": {"_pre_command": f"mkdir -p f{i}/b{j}; "},
                },
                [f"f{i}/b{j}/foo{i}.txt"],
                {
                    "rule": "copy",
                    "inputs": [f"bar{j}.txt"],
                    "outputs": [f"f{i}/b{j}/bar{j}.txt"],
                    "variables": {"_pre_command": f"mkdir -p f{i}/b{j}; "},
                },
                [f"f{i}/b{j}/bar{j}.txt"],
            ]
            assert ns == []
    assert len(results) == 0


def test_generate_anonymous_wildcard_inp_out(tmpdir):
    tmpdir = str(tmpdir)
    gen = BuildGenerator(copy, ["foo*.txt"], ["bar/"])
    previous_outputs = {"foo1.txt", "foo3.txt"}
    with contextlib.chdir(tmpdir):
        results = list(gen(previous_outputs, set()))
    [[records, ns]] = results
    assert records == [
        "command: copy",
        "inp: foo1.txt foo3.txt",
        "out: bar/",
        {
            "rule": "copy",
            "outputs": ["bar/foo1.txt"],
            "inputs": ["foo1.txt"],
            "variables": {"_pre_command": "mkdir -p bar; "},
        },
        ["bar/foo1.txt"],
        {
            "rule": "copy",
            "outputs": ["bar/foo3.txt"],
            "inputs": ["foo3.txt"],
            "variables": {"_pre_command": "mkdir -p bar; "},
        },
        ["bar/foo3.txt"],
    ]
    assert ns == []


def test_generate_named_wildcard_inp_inp_out_mismatch(tmpdir):
    tmpdir = str(tmpdir)
    gen = BuildGenerator(copy, ["foo${*id}.txt", "bar.txt"], ["spam${*id}/"])
    previous_outputs = {"foo1.txt", "foo3.txt"}
    with contextlib.chdir(tmpdir):
        with pytest.raises(ValueError):
            list(gen(previous_outputs, set()))


def test_generate_named_wildcard_inp_inp_out_match(tmpdir):
    tmpdir = str(tmpdir)
    gen = BuildGenerator(copy, ["foo${*id}.txt", "bar${*id}.txt"], ["spam${*id}/"])
    previous_outputs = {"foo3.txt", "bar3.txt"}
    with contextlib.chdir(tmpdir):
        results = list(gen(previous_outputs, set()))
    records, ns = results[0]
    assert records == [
        "command: copy",
        "inp: foo3.txt bar3.txt",
        "out: spam3/",
        {
            "rule": "copy",
            "outputs": ["spam3/foo3.txt"],
            "inputs": ["foo3.txt"],
            "variables": {"_pre_command": "mkdir -p spam3; "},
        },
        ["spam3/foo3.txt"],
        {
            "rule": "copy",
            "outputs": ["spam3/bar3.txt"],
            "inputs": ["bar3.txt"],
            "variables": {"_pre_command": "mkdir -p spam3; "},
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
    constants = {"ignore_missing": "foo*"} if ignore else {}
    gen = BuildGenerator(python_script, ["script.py"], [], constants)
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


LOGO_SVG = """\
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewbox="0 0 100 100">
<circle cx="0" cy="50" r="30" fill="00AA00"  stroke="#AA00AA" stroke-width="10" />
</svg>
"""


def test_generate_constants(tmpdir):
    tmpdir = str(tmpdir)
    tpldir = os.path.join(tmpdir, "template")
    os.mkdir(tpldir)
    with open(os.path.join(tpldir, "logo.svg"), "w") as fh:
        fh.write(LOGO_SVG)
    gen = BuildGenerator(
        convert_svg_pdf,
        ["template/logo.svg"],
        ["public/logo.pdf"],
        {"inkscape": "my-special-inkscape"},
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
            "rule": "convert_svg_pdf",
            "outputs": ["public/logo.pdf"],
            "pool": "convert_svg_pdf",
            "inputs": ["template/logo.svg"],
            "variables": {"_pre_command": "mkdir -p public; ", "inkscape": "my-special-inkscape"},
        },
        ["public/logo.pdf"],
    ]
    assert ns == ["template/logo.svg"]


def test_generate_no_defaults(tmpdir):
    tmpdir = str(tmpdir)
    gen = BuildGenerator(copy, ["README.md"], ["public/README.md"], default=False)
    previous_outputs = {"README.md"}
    with contextlib.chdir(tmpdir):
        results = list(gen(previous_outputs, set()))
    [[records, ns]] = results
    assert records == [
        "command: copy",
        "inp: README.md",
        "out: public/README.md",
        {
            "rule": "copy",
            "outputs": ["public/README.md"],
            "inputs": ["README.md"],
            "variables": {"_pre_command": "mkdir -p public; "},
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
    gen = BuildGenerator(latex, ["main.tex"], [], default=False)
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
