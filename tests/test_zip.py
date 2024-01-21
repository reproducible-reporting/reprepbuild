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
"""Unit tests for reprepbuild.builtin.zip"""


from reprepbuild.builtin.zip import zip_latex, zip_manifest, zip_plain

BUILDS_ZIP_MANIFEST = [
    {
        "rule": "zip_manifest",
        "inputs": ["sub/WAWA.sha256"],
        "outputs": ["sub.zip"],
        "pool": "console",
    }
]


def test_write_build_zip_manifest():
    builds, _ = zip_manifest.generate(["sub/WAWA.sha256"], ["sub.zip"], None)
    assert BUILDS_ZIP_MANIFEST == builds


BUILDS_ZIP_LATEX = [
    {
        "rule": "zip_latex",
        "inputs": ["latex-sub/sub.fls"],
        "implicit_outputs": ["latex-sub/sub.sha256"],
        "outputs": ["sub.zip"],
        "pool": "console",
    }
]


def test_write_build_zip_latex():
    builds, _ = zip_latex.generate(["latex-sub/sub.fls"], ["sub.zip"], None)
    assert BUILDS_ZIP_LATEX == builds


BUILDS_ZIP_PLAIN1 = [
    {
        "rule": "zip_plain",
        "inputs": ["a/data1.txt", "a/data2.txt", "a/fig.png"],
        "implicit_outputs": ["a/something.sha256"],
        "outputs": ["something.zip"],
        "pool": "console",
    }
]


def test_write_build_zip_plain1a():
    builds, _ = zip_plain.generate(
        ["a/data1.txt", "a/data2.txt", "a/fig.png", "a/something.sha256"], ["something.zip"], None
    )
    assert BUILDS_ZIP_PLAIN1 == builds


def test_write_build_zip_plain1b():
    builds, _ = zip_plain.generate(
        ["a/data1.txt", "a/data2.txt", "a/fig.png"], ["something.zip"], None
    )
    assert BUILDS_ZIP_PLAIN1 == builds


BUILDS_ZIP_PLAIN2 = [
    {
        "rule": "zip_plain",
        "inputs": ["foo.txt", "bar.csv"],
        "implicit_outputs": ["data.sha256"],
        "outputs": ["data.zip"],
        "pool": "console",
    }
]


def test_write_build_zip_plain2a():
    builds, _ = zip_plain.generate(
        ["foo.txt", "bar.csv", "data.sha256", "data.zip"], ["data.zip"], None
    )
    assert BUILDS_ZIP_PLAIN2 == builds


def test_write_build_zip_plain2b():
    builds, _ = zip_plain.generate(["foo.txt", "bar.csv"], ["data.zip"], None)
    assert BUILDS_ZIP_PLAIN2 == builds
