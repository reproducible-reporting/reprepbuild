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
"""Unit tests for reprepbuild.scripts.render"""

import os

try:
    import fitz_new as fitz
except ImportError:
    import fitz

from reprepbuild.scripts.markdown_pdf import convert_markdown
from reprepbuild.scripts.pdf_nup import pdf_nup


def test_pdf_nup(tmpdir):
    path_pdf1 = os.path.join(tmpdir, "doc1.pdf")
    convert_markdown("word1 word2", fn_pdf=path_pdf1)
    assert os.path.isfile(path_pdf1)
    with fitz.open(path_pdf1) as doc1:
        assert doc1[0].get_text().strip() == "word1 word2"
    path_pdf2 = os.path.join(tmpdir, "doc2.pdf")
    pdf_nup(path_pdf1, 2, 2, 10.0, 297.0, 210.0, path_pdf2)
    assert os.path.isfile(path_pdf1)
    with fitz.open(path_pdf2) as doc2:
        assert doc2[0].get_text().strip() == "word1 word2"
