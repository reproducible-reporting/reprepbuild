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
"""Unit tests for reprepbuild.builtin.transform"""


from reprepbuild.builtin.transform import convert_odf_pdf, convert_svg_pdf, copy, pdf_raster, render

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
    builds, _ = copy.generate(["sub/foo.txt", "sub/bar.md"], ["/dst/sub/"], None, {})
    assert BUILDS_COPY == builds


BUILDS_COPY_AS = [
    {
        "rule": "copy",
        "inputs": ["sub/foo.txt"],
        "outputs": ["/dst/sub/bar.txt"],
    }
]


def test_write_build_copy_as():
    builds, _ = copy.generate(["sub/foo.txt"], ["/dst/sub/bar.txt"], None, {})
    assert BUILDS_COPY_AS == builds


BUILDS_RENDER = [
    {
        "rule": "render",
        "implicit": ["${here}/.reprepbuild/variables.json"],
        "inputs": ["sub/foo.md"],
        "outputs": ["/dst/sub/foo.md"],
    },
    {
        "rule": "render",
        "implicit": ["${here}/.reprepbuild/variables.json"],
        "inputs": ["sub/bar.tex"],
        "outputs": ["/dst/sub/bar.tex"],
    },
]


def test_write_build_render():
    builds, _ = render.generate(["sub/foo.md", "sub/bar.tex"], ["/dst/sub/"], None, {})
    assert BUILDS_RENDER == builds


BUILDS_CONVERT_SVG_PDF1 = [
    {
        "rule": "convert_svg_pdf",
        "pool": "convert_svg_pdf",
        "inputs": ["sub/foo.svg"],
        "outputs": ["/dst/sub/foo.pdf"],
        "variables": {"inkscape": "inkscape"},
    }
]


def test_write_build_convert_svg_pdf1():
    builds, _ = convert_svg_pdf.generate(["sub/foo.svg"], ["/dst/sub/"], None, {})
    assert BUILDS_CONVERT_SVG_PDF1 == builds


BUILDS_CONVERT_SVG_PDF2 = [
    {
        "rule": "convert_svg_pdf",
        "pool": "convert_svg_pdf",
        "inputs": ["sub/foo.svg"],
        "outputs": ["sub/foo.pdf"],
        "variables": {"inkscape": "inkscape"},
    }
]


def test_write_build_convert_svg_pdf2():
    builds, _ = convert_svg_pdf.generate(["sub/foo.svg"], [], None, {})
    assert BUILDS_CONVERT_SVG_PDF2 == builds


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


def test_write_build_convert_svg_pdf3():
    builds, _ = convert_svg_pdf.generate(["sub/foo.svg", "sub/bar.svg"], [], None, {})
    assert BUILDS_CONVERT_SVG_PDF3 == builds


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
    builds, _ = convert_odf_pdf.generate(["sub/foo.odp"], ["/dst/sub/"], None, {})
    assert BUILDS_CONVERT_ODF_PDF == builds


BUILDS_CONVERT_PDF_RASTER = [
    {
        "rule": "pdf_raster",
        "inputs": ["original.pdf"],
        "outputs": ["/public/rastered.pdf"],
        "variables": {"gs": "gs", "raster_dpi": "150"},
    }
]


def test_write_build_pdf_raster():
    builds, _ = pdf_raster.generate(["original.pdf"], ["/public/rastered.pdf"], None, {})
    assert BUILDS_CONVERT_PDF_RASTER == builds
