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
import re
import subprocess
import sys

from .utils import write_depfile
from .zip import reprozip


def main():
    """Main program."""
    args = parse_args()
    article_zip(args.fn_zip, args.fn_pdf)


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
        sys.exit(2)
    prefix = filename[:-4]

    # Collect files to be zipped
    paths = []
    with open(os.path.join(workdir, prefix + ".fls")) as f:
        for line in f:
            if not line.startswith("INPUT "):
                continue
            path = line[6:].strip()
            if path.startswith("/"):
                continue
            if re.match(r".*\.aux$", path):
                continue
            path = os.path.normpath(path)
            path = os.path.join(workdir, path)
            paths.append(path)

    # Write zip
    reprozip(fn_zip, list(paths))


if __name__ == "__main__":
    main()
