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
"""Creation and validation of MANIFEST files.

There are two kinds of MANIFEST files:

- ``MANIFEST.in`` contains rules to select or ignore files to be included into an archive.
- ``MANIFEST.sha265`` is the result of a processing a ``MANIFEST.in`` file with this script.
  It contains every individual file, together with its size in bytes and its sha256 sum.
  This file is a suitable input for the script ``rr-zip``
"""


import argparse
import hashlib
import sys

from setuptools.command.egg_info import FileList
from tqdm import tqdm


def main() -> int:
    """Main program."""
    args = parse_args()
    if not args.manifest_in.endswith(".in"):
        raise ValueError("The manifest input file must end with .in")

    # Collect the complete list of files.
    filelist = FileList()
    with open(args.manifest_in) as f:
        for line in f:
            line = line[: line.find("#")].strip()
            if line != "":
                filelist.process_template_line(line)
    filelist.sort()
    filelist.remove_duplicates()

    # Build the full file list with file sizes and SHA256 sums.
    with open(args.manifest_in[:-3] + ".sha256", "w") as f:
        for fn in tqdm(filelist.files, delay=1):
            size, sha256 = compute_sha256(fn)
            f.write(f"{size:15d} {sha256} {fn}\n")
    return 0


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="rr-manifest", description="Create a MANIFEST.sha256 file for rr-zip."
    )
    parser.add_argument("manifest_in", help="A MANIFEST.in file compatible with setuptools.")
    args = parser.parse_args()
    return args


def compute_sha256(path: str) -> tuple[int, str]:
    """Compute SHA256 hash and size in bytes of a file."""
    size = 0
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            block = f.read(1048576)
            size += len(block)
            if len(block) == 0:
                break
            sha.update(block)
    return size, sha.hexdigest()


if __name__ == "__main__":
    sys.exit(main())
