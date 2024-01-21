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
"""Unit tests for reprepbuild.builtin.mupdf"""


from reprepbuild.builtin.mupdf import pdf_add_notes, pdf_merge, pdf_nup

BUILDS_PDF_MERGE = [
    {
        "rule": "pdf_merge",
        "inputs": ["part1.pdf", "part2.pdf", "part3.pdf", "part4.pdf"],
        "outputs": ["foo/merged.pdf"],
        "variables": {"mutool": "mutool"},
    }
]


def test_write_build_pdf_merge():
    builds, _ = pdf_merge.generate(
        ["part1.pdf", "part2.pdf", "part3.pdf", "part4.pdf"], ["foo/merged.pdf"], None
    )
    assert BUILDS_PDF_MERGE == builds


BUILDS_PDF_ADD_NOTES = [
    {
        "rule": "pdf_add_notes",
        "inputs": ["src.pdf", "notes.pdf"],
        "outputs": ["dst.pdf"],
    }
]


def test_write_build_pdf_add_notes():
    builds, _ = pdf_add_notes.generate(["src.pdf", "notes.pdf"], ["dst.pdf"], None)
    assert BUILDS_PDF_ADD_NOTES == builds


BUILDS_PDF_NUP = [
    {
        "rule": "pdf_nup",
        "inputs": ["src.pdf"],
        "outputs": ["dst.pdf"],
        "variables": {
            "nrow": "3",
            "ncol": "2",
            "margin": "10.000",
            "width": "210.000",
            "height": "297.000",
        },
    }
]


def test_write_build_pdf_nup():
    builds, _ = pdf_nup.generate(["src.pdf"], ["dst.pdf"], [3, 2, 10.0, 210.0, 297.0])
    assert BUILDS_PDF_NUP == builds
