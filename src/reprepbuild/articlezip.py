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
"""Create a reproducible zip file of the main document sources."""

import argparse
import os

from .utils import parse_inputs_fls
from .zip import reprozip


def main():
    """Main program."""
    args = parse_args()
    return article_zip(args.path_zip, args.path_pdf)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser("rr-article-zip")
    parser.add_argument("path_zip", help="The output zip file with the sources.")
    parser.add_argument("path_pdf", help="The article pdf file.")
    return parser.parse_args()


def article_zip(path_zip, path_pdf):
    """Zip the sources of the article."""
    if not path_pdf.endswith(".pdf"):
        print(f"Article PDF must have a `.pdf` extension. Got {path_pdf}")
        return 2
    workdir, fn_py = os.path.split(path_pdf)
    prefix = fn_py[:-4]

    # Collect files to be zipped and write zip
    reprozip(path_zip, parse_inputs_fls(os.path.join(workdir, prefix + ".fls")))
    return 0


if __name__ == "__main__":
    main()
