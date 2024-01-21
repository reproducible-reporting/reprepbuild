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
"""Unit tests for reprepbuild.builtin.transform"""

import contextlib
import os

from reprepbuild.builtin.transform import (
    convert_odf_pdf,
    convert_pdf_png,
    convert_svg_pdf,
    copy,
    markdown_pdf,
    pdf_raster,
)

BUILDS_COPY = [
    {
        "rule": "copy",
        "inputs": ["sub/foo.txt"],
        "outputs": ["/dst/sub/foo.txt"],
    },
    {
        "rule": "copy",
        "inputs": ["sub/bar.md"],
        "outputs": ["/dst/sub/bar.md"],
    },
]


def test_write_build_copy():
    builds, _ = copy.generate(["sub/foo.txt", "sub/bar.md"], ["/dst/sub/"], None)
    assert BUILDS_COPY == builds


BUILDS_COPY_AS = [
    {
        "rule": "copy",
        "inputs": ["sub/foo.txt"],
        "outputs": ["/dst/sub/bar.txt"],
    }
]


def test_write_build_copy_as():
    builds, _ = copy.generate(["sub/foo.txt"], ["/dst/sub/bar.txt"], None)
    assert BUILDS_COPY_AS == builds


BUILDS_CONVERT_SVG_PDF1 = [
    {
        "rule": "convert_svg_pdf",
        "pool": "convert_svg_pdf",
        "inputs": ["sub/foo.svg"],
        "outputs": ["/dst/sub/foo.pdf"],
        "variables": {"inkscape": "inkscape"},
    }
]


MINIMAL_SVG = '<svg xmlns="http://www.w3.org/2000/svg"></svg>'


def test_write_build_convert_svg_pdf1(tmpdir):
    with contextlib.chdir(tmpdir):
        os.mkdir("sub")
        with open("sub/foo.svg", "w") as fh:
            fh.write(MINIMAL_SVG)
        builds, gendeps = convert_svg_pdf.generate(["sub/foo.svg"], ["/dst/sub/"], None)
    assert BUILDS_CONVERT_SVG_PDF1 == builds
    assert gendeps == ["sub/foo.svg"]


BUILDS_CONVERT_SVG_PDF2 = [
    {
        "rule": "convert_svg_pdf",
        "pool": "convert_svg_pdf",
        "inputs": ["sub/foo.svg"],
        "outputs": ["sub/foo.pdf"],
        "variables": {"inkscape": "inkscape"},
    }
]


def test_write_build_convert_svg_pdf2(tmpdir):
    with contextlib.chdir(tmpdir):
        os.mkdir("sub")
        with open("sub/foo.svg", "w") as fh:
            fh.write(MINIMAL_SVG)
        builds, gendeps = convert_svg_pdf.generate(["sub/foo.svg"], [], None)
    assert BUILDS_CONVERT_SVG_PDF2 == builds
    assert gendeps == ["sub/foo.svg"]


BUILDS_CONVERT_SVG_PDF3 = [
    {
        "rule": "convert_svg_pdf",
        "pool": "convert_svg_pdf",
        "inputs": ["sub/foo.svg"],
        "outputs": ["sub/foo.pdf"],
        "variables": {"inkscape": "inkscape"},
    },
    {
        "rule": "convert_svg_pdf",
        "pool": "convert_svg_pdf",
        "inputs": ["sub/bar.svg"],
        "outputs": ["sub/bar.pdf"],
        "variables": {"inkscape": "inkscape"},
    },
]


def test_write_build_convert_svg_pdf3(tmpdir):
    with contextlib.chdir(tmpdir):
        os.mkdir("sub")
        with open("sub/foo.svg", "w") as fh:
            fh.write(MINIMAL_SVG)
        with open("sub/bar.svg", "w") as fh:
            fh.write(MINIMAL_SVG)
        builds, gendeps = convert_svg_pdf.generate(["sub/foo.svg", "sub/bar.svg"], [], None)
    assert BUILDS_CONVERT_SVG_PDF3 == builds
    assert gendeps == ["sub/foo.svg", "sub/bar.svg"]


CONTAINER_SVG = """\
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewbox="0 0 100 100">
<image x="0" y="10" href="image.png" width="50" height="30" />
<image x="50" y="10" href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcS\
JAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==" width="50" height="30" />
</svg>
"""

BUILDS_CONVERT_SVG_PDF_CONTAINER = [
    {
        "rule": "convert_svg_pdf",
        "pool": "convert_svg_pdf",
        "inputs": ["sub/container.svg"],
        "implicit": ["sub/image.png"],
        "outputs": ["sub/container.pdf"],
        "variables": {"inkscape": "inkscape"},
    }
]


def test_write_build_convert_svg_pdf_container(tmpdir):
    with contextlib.chdir(tmpdir):
        os.mkdir("sub")
        with open("sub/container.svg", "w") as fh:
            fh.write(CONTAINER_SVG)
        builds, gendeps = convert_svg_pdf.generate(["sub/container.svg"], [], None)
    assert BUILDS_CONVERT_SVG_PDF_CONTAINER == builds
    assert gendeps == ["sub/container.svg"]


OUTER_CONTAINER_SVG = """\
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:svg="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     width="100" height="100" viewbox="0 0 100 100">
<image x="0" y="10" xlink:href="file://container.svg" widht="30" height="40" />
</svg>
"""


BUILDS_CONVERT_SVG_PDF_OUTER_CONTAINER = [
    {
        "rule": "convert_svg_pdf",
        "pool": "convert_svg_pdf",
        "inputs": ["outer.svg"],
        "implicit": ["container.svg", "image.png"],
        "outputs": ["outer.pdf"],
        "variables": {"inkscape": "inkscape"},
    }
]


def test_write_build_convert_svg_pdf_outer_container(tmpdir):
    with contextlib.chdir(tmpdir):
        with open("outer.svg", "w") as fh:
            fh.write(OUTER_CONTAINER_SVG)
        with open("container.svg", "w") as fh:
            fh.write(CONTAINER_SVG)
        builds, gendeps = convert_svg_pdf.generate(["outer.svg"], [], None)
    assert BUILDS_CONVERT_SVG_PDF_OUTER_CONTAINER == builds
    assert gendeps == ["outer.svg", "container.svg"]


BUILDS_CONVERT_ODF_PDF = [
    {
        "rule": "convert_odf_pdf",
        "pool": "convert_odf_pdf",
        "inputs": ["sub/foo.odp"],
        "outputs": ["/dst/sub/foo.pdf"],
        "variables": {"libreoffice": "libreoffice"},
    }
]


def test_write_build_convert_odf_pdf():
    builds, _ = convert_odf_pdf.generate(["sub/foo.odp"], ["/dst/sub/"], None)
    assert BUILDS_CONVERT_ODF_PDF == builds


BUILDS_CONVERT_PDF_PNG = [
    {
        "rule": "convert_pdf_png",
        "inputs": ["sub/foo.pdf"],
        "outputs": ["/dst/sub/foo.png"],
        "variables": {"mutool": "mutool", "dpi": "600"},
    }
]


def test_write_build_convert_pdf_png():
    builds, _ = convert_pdf_png.generate(["sub/foo.pdf"], ["/dst/sub/"], None)
    assert BUILDS_CONVERT_PDF_PNG == builds


BUILDS_CONVERT_PDF_RASTER = [
    {
        "rule": "pdf_raster",
        "inputs": ["original.pdf"],
        "outputs": ["/public/rastered.pdf"],
        "variables": {"gs": "gs", "raster_dpi": "150"},
    }
]


def test_write_build_pdf_raster():
    builds, _ = pdf_raster.generate(["original.pdf"], ["/public/rastered.pdf"], None)
    assert BUILDS_CONVERT_PDF_RASTER == builds


BUILDS_CONVERT_MARKDOWN_PDF = [
    {
        "rule": "markdown_pdf",
        "inputs": ["original.md"],
        "outputs": ["/public/original.pdf"],
    }
]


def test_write_build_markdown_pdf():
    builds, _ = markdown_pdf.generate(["original.md"], ["/public/"], None)
    assert BUILDS_CONVERT_MARKDOWN_PDF == builds
