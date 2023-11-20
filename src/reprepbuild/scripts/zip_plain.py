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
"""Create reproducible zip files of files provided on the command line."""

import argparse
import os
import sys

from .manifest import compute_sha256
from .zip_manifest import make_zip_manifest


def main() -> int:
    """Main program."""
    args = parse_args()
    return make_zip_plain(args.paths_in, args.path_zip)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser("rr-zip-plain", description="Zip a set of files.")
    parser.add_argument("paths_in", help="Paths to include in the ZIP file.", nargs="+")
    parser.add_argument("path_zip", help="The output zip file with the sources.")
    return parser.parse_args()


def make_zip_plain(paths_in: str, path_zip: str) -> int:
    """Zip the sources of the article."""
    if not path_zip.endswith(".zip"):
        raise ValueError("The ZIP file must end with extension .zip.")
    prefix = path_zip[:-4]
    # The manifest is stored as deep in the dir tree as possible, using commonpath.
    workdir = os.path.commonpath(paths_in)
    path_manifest = os.path.join(workdir, os.path.basename(prefix) + ".sha256")
    with open(path_manifest, "w") as f:
        for path_in in paths_in:
            size, sha256 = compute_sha256(path_in)
            f.write(f"{size:15d} {sha256} {path_in[len(workdir) + 1:]}\n")

    # Collect files to be zipped and write zip
    return make_zip_manifest(path_manifest, path_zip, check_sha256=False)


if __name__ == "__main__":
    sys.exit(main())
