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
"""Create reproducible zip files, by ignoring time stamps."""


import argparse
import hashlib
import os
import zipfile

import tqdm

__all__ = ("reprozip",)


def main():
    """Main program."""
    args = parse_args()
    reprozip(args.path_zip, args.path_man)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser("rr-zip")
    parser.add_argument("path_zip", help="Destination zip file.")
    parser.add_argument(
        "path_man",
        help="The MANIFEST.sha256 with all files to be zipped. "
        "The sha256 sums of the files will be checked before archiving. "
        "The manifest file will be included in the ZIP.",
    )
    return parser.parse_args()


def reprozip(path_zip, path_man, check_sha256=True):
    """Create a reproducible zip file."""
    if not path_zip.endswith(".zip"):
        print(f"Destination must have a `.zip` extension. Got {path_zip}")
        return 2
    if not path_man.endswith(".sha256"):
        print(f"Manifest file must have a `.sha256` extension. Got {path_man}")
        return 2

    # Load the list of files and check the sha256
    paths_in = [path_man]
    root = os.path.dirname(path_man)
    with open(path_man) as f:
        lines = f.readlines()
    for line in tqdm.tqdm(lines, f"Checking {path_man}", delay=1):
        path = os.path.join(root, line[66:].strip())
        if check_sha256:
            sha256 = line[:64].lower()
            mysha256 = compute_sha256(path)
            if sha256 != mysha256:
                print(f"SHA256 mismatch for file: {mysha256}  {path}")
                return 2
        paths_in.append(path)

    # Remove old zip
    if os.path.isfile(path_zip):
        os.remove(path_zip)

    # Clean up list of input paths
    paths_in = sorted({os.path.normpath(path_in) for path_in in paths_in})
    nskip = len(root) + 1
    # Make a new zip file
    with zipfile.ZipFile(path_zip, "w") as fz:
        for path_in in tqdm.tqdm(paths_in, f"Creating {path_zip}", delay=1):
            with open(path_in, "rb") as fin:
                zipinfo = zipfile.ZipInfo(path_in[nskip:])
                zipinfo.compress_type = zipfile.ZIP_DEFLATED
                fz.writestr(zipinfo, fin.read())


def compute_sha256(path: str):
    """Compute SHA256 hash of a file."""
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            block = f.read(1048576)
            if len(block) == 0:
                break
            sha.update(block)
    return sha.hexdigest()


if __name__ == "__main__":
    main()
