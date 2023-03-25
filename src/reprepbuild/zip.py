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
import os
import zipfile

__all__ = ("reprozip",)


def main():
    """Main program."""
    args = parse_args()
    reprozip(args.path_zip, args.paths_in)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser("rr-zip")
    parser.add_argument("path_zip", help="Destination zip file.")
    parser.add_argument("paths_in", nargs="+", help="File paths to zip.")
    return parser.parse_args()


def reprozip(path_zip, paths_in):
    """Create a reproducible zip file."""
    if not path_zip.endswith(".zip"):
        print(f"Destination must have a `.zip` extension. Got {path_zip}")
        return 2
    # Remove old zip
    if os.path.isfile(path_zip):
        os.remove(path_zip)
    # Clean up list of input paths
    paths_in = sorted({os.path.normpath(path_in) for path_in in paths_in})
    # Prepare to trim leading directories
    if len(paths_in) == 1:
        common = os.path.dirname(paths_in[0])
    else:
        common = os.path.commonpath(paths_in)
    assert not common.endswith("/")
    nskip = len(common) + 1
    # Make a new zip file
    with zipfile.ZipFile(path_zip, "w") as fz:
        for path_in in paths_in:
            with open(path_in, "rb") as fin:
                zipinfo = zipfile.ZipInfo(path_in[nskip:])
                zipinfo.compress_type = zipfile.ZIP_LZMA
                fz.writestr(zipinfo, fin.read())


if __name__ == "__main__":
    main()
