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

from ..utils import parse_inputs_fls
from .manifest import compute_sha256
from .zip import reprozip


def main():
    """Main program."""
    args = parse_args()
    return article_zip(args.path_fls, args.path_zip)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        "rr-latex-zip", description="Zip a LaTeX file with required files."
    )
    parser.add_argument("path_fls", help="The LaTeX fls file.")
    parser.add_argument("path_zip", help="The output zip file with the sources.")
    return parser.parse_args()


def article_zip(path_fls: str, path_zip: str):
    """Zip the sources of the article."""
    if not path_fls.endswith(".fls"):
        print(f"The input must have a `.fls` extension. Got {path_fls}")
        return 2
    workdir, fn_fls = os.path.split(path_fls)
    prefix = fn_fls[:-4]

    # Make a manifest file
    paths_in = parse_inputs_fls(path_fls)
    path_manifest = f"{workdir}/{prefix}.sha256"
    with open(path_manifest, "w") as f:
        for path_in in paths_in:
            size, sha256 = compute_sha256(path_in)
            f.write(f"{size:15d} {sha256} {path_in[len(workdir) + 1:]}\n")

    # Collect files to be zipped and write zip
    return reprozip(path_manifest, path_zip, check_sha256=False)


if __name__ == "__main__":
    main()
