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
"""Script to insert notes pages at every even page in a PDF."""

import argparse
import sys

try:
    import fitz_new as fitz
except ImportError:
    import fitz


__all__ = ("pdf_add_notes",)


def main() -> int:
    """Main program."""
    args = parse_args()
    pdf_add_notes(args.path_src, args.path_notes, args.path_dst)
    return 0


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="rr-add-notes-pdf", description="Add a notes page at every even page of a PDF file."
    )
    parser.add_argument("path_src", help="The source pdf to which notes should be added.")
    parser.add_argument("path_notes", help="The pdf with the notes page(s).")
    parser.add_argument("path_dst", help="The output pdf.")
    return parser.parse_args()


def pdf_add_notes(path_src: str, path_notes: str, path_dst: str):
    """Insert notes pages at every even page."""
    for path_pdf in path_src, path_notes, path_dst:
        if not path_pdf.endswith(".pdf"):
            print(f"All arguments must have a `.pdf` extension, got: {path_pdf}")
            return 2
    src = fitz.open(path_src)
    notes = fitz.open(path_notes)
    dst = fitz.open()
    for isrc in range(len(src)):
        final = isrc == len(src) - 1
        dst.insert_pdf(src, from_page=isrc, to_page=isrc, final=final)
        inotes = isrc % len(notes)
        dst.insert_pdf(notes, from_page=inotes, to_page=inotes, final=final)
    dst.xref_set_key(-1, "ID", "null")
    dst.save(path_dst, garbage=4, deflate=True)
    dst.close()
    src.close()
    notes.close()


if __name__ == "__main__":
    sys.exit(main())
