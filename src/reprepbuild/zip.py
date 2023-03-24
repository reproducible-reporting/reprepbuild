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
    reprozip(args.fn_zip, args.fns)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser("rr-zip")
    parser.add_argument("fn_zip", help="Destination zip file.")
    parser.add_argument("fns", nargs="+", help="Files to zip.")
    return parser.parse_args()


def reprozip(fn_zip, filenames):
    """Create a reproducible zip file."""
    # Remove old zip
    if os.path.isfile(fn_zip):
        os.remove(fn_zip)
    # Clean up list of filenames
    filenames = sorted({os.path.normpath(filename) for filename in filenames})
    # Prepare to trim leading directories
    if len(filenames) == 1:
        common = os.path.dirname(filenames[0])
    else:
        common = os.path.commonpath(filenames)
    assert not common.endswith("/")
    nskip = len(common) + 1
    # Make a new zip file
    with zipfile.ZipFile(fn_zip, "w") as fz:
        for filename in filenames:
            with open(filename, "rb") as fin:
                zipinfo = zipfile.ZipInfo(filename[nskip:])
                zipinfo.compress_type = zipfile.ZIP_LZMA
                fz.writestr(zipinfo, fin.read())


if __name__ == "__main__":
    main()
