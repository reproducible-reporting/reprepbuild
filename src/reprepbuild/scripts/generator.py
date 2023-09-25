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
"""Write the ``build.ninja`` file."""


import argparse
import os
import sys

from ..__main__ import generate


def main() -> int:
    """Main program."""
    args = parse_args()
    generate(args.root)
    return 0


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser("rr-generator", description="Write a build.ninja file")
    parser.add_argument(
        "root", default=os.getcwd(), help="Directory containing the top-level reprepbuild.yaml file"
    )
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
