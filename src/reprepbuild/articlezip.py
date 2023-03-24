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
    return article_zip(args.fn_zip, args.fn_pdf)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser("rr-article-zip")
    parser.add_argument("fn_zip", help="The output zip file with the sources.")
    parser.add_argument("fn_pdf", help="The article pdf file.")
    return parser.parse_args()


def article_zip(fn_zip, fn_pdf):
    """Zip the sources of the article."""
    workdir, filename = os.path.split(fn_pdf)
    if not filename.endswith(".pdf"):
        print(f"An article must have a pdf extension. Got {workdir}/{filename}")
        return 2
    prefix = filename[:-4]

    # Collect files to be zipped and write zip
    reprozip(fn_zip, parse_inputs_fls(os.path.join(workdir, prefix + ".fls")))
    return 0


if __name__ == "__main__":
    main()
