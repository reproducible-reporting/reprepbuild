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
"""Utilities used by other reprepbuild modules."""

import argparse
import os
import shutil
import tempfile

import fitz

__all__ = ("normalize_pdf",)


def main():
    """Main program."""
    normalize_pdf(parse_args().fn_pdf)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser("rr-normalize-pdf")
    parser.add_argument("fn_pdf", help="The pdf to be normalized (in place).")
    return parser.parse_args()


def normalize_pdf(fn_pdf):
    """Rewrite a PDF by its normalized equivalent. This helps making PDFs reproducible."""
    pdf = fitz.open(fn_pdf)
    pdf.set_metadata({})
    pdf.del_xml_metadata()
    pdf.scrub()
    with tempfile.TemporaryDirectory(suffix="normalize-pdf", prefix="rr") as dn:
        fn_out = os.path.join(dn, "out.pdf")
        pdf.save(fn_out, garbage=4, deflate=True, linear=True, no_new_id=True)
        pdf.close()
        shutil.copy(fn_out, fn_pdf)


if __name__ == "__main__":
    main()
