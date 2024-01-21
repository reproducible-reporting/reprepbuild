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
"""Put multiple pages in a single page, using a fixed layout."""

import argparse
import sys

try:
    import fitz_new as fitz
except ImportError:
    import fitz


__all__ = ("pdf_nup",)


def main() -> int:
    """Main program."""
    args = parse_args()
    pdf_nup(
        args.path_src, args.nrow, args.ncol, args.margin, args.width, args.height, args.path_dst
    )
    return 0


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="rr-nup-pdf", description="Put multiple pages in a single page, using a fixed layout."
    )
    parser.add_argument("path_src", help="The source pdf to which notes should be added.")
    parser.add_argument("nrow", help="The number of rows.", type=int)
    parser.add_argument("ncol", help="The number of columns.", type=int)
    parser.add_argument("margin", help="The margin in mm", type=float)
    parser.add_argument("width", help="The page width in mm", type=float)
    parser.add_argument("height", help="The page height in mm", type=float)
    parser.add_argument("path_dst", help="The output pdf.")
    return parser.parse_args()


def pdf_nup(
    path_src: str, nrow: int, ncol: int, margin: float, width: float, height: float, path_dst: str
):
    """Put multiple pages in a single page, using a fixed layout.

    Parameters
    ----------
    path_src
        The source PDF filename.
    nrow
        The number of rows in the layout.
    ncol
        The number of columns in the layout.
    margin
        The margin and (minimal) spacing between small pages in millimeter.
    width
        The output page width in millimeter.
    height
        The output page height in millimeter.
    path_dst
        The destination PDF filename.
    """
    for path_pdf in path_src, path_dst:
        if not path_pdf.endswith(".pdf"):
            print(f"All arguments must have a `.pdf` extension, got: {path_pdf}")
            return 2
    src = fitz.open(path_src)
    dst = fitz.open()

    nup = nrow * ncol
    unit = 72 / 25.4
    # Convert distances in mm to points
    margin *= unit
    width *= unit
    height *= unit

    # Spacing between two top-left corners of neighboring panels.
    xshift = (width - margin) / ncol
    yshift = (height - margin) / nrow

    # double loop adding all (small) pages to the destination PDF.
    for icoarse in range(0, len(src), nup):
        dst_page = dst.new_page(width=width, height=height)
        for ifine in range(icoarse, min(icoarse + nup, len(src))):
            ioffset = ifine - icoarse
            irow = ioffset // ncol
            icol = ioffset % ncol
            dst_page.show_pdf_page(
                fitz.Rect(
                    margin + xshift * icol,
                    margin + yshift * irow,
                    xshift * (icol + 1),
                    yshift * (irow + 1),
                ),
                src,
                ifine,
            )
    dst.xref_set_key(-1, "ID", "null")
    dst.save(path_dst, garbage=4, deflate=True)
    dst.close()
    src.close()


if __name__ == "__main__":
    sys.exit(main())
