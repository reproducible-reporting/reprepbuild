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
r"""Execute a shell script.

This script is currently only a stub, possibly extended with more features later.
"""

import argparse
import os
import subprocess
import sys


def main() -> int:
    """Main program."""
    args = parse_args()
    return run_script(args.path_sh)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(prog="rr-shell-script", description="Execute a shell script")
    parser.add_argument("path_sh", help="The shell script to be executed.")
    return parser.parse_args()


def run_script(path_sh) -> int:
    """Run the Shell script in its own directory.

    Parameters
    ----------
    path_sh
        The full path of the script.
        (It will be executed after changing directory.)

    Returns
    -------
    exitcode
        The script exitcode.
    """
    # Process path_sh
    if not path_sh.endswith(".sh"):
        print(f"Shell script must have a .sh extension. Got {path_sh}")
        return 2
    workdir, fn_sh = os.path.split(path_sh)
    workdir = os.path.normpath(workdir)
    p = subprocess.run(
        ["./" + fn_sh],
        check=False,
        cwd=workdir,
        env=os.environ | {"SOURCE_DATE_EPOCH": "315532800"},
    )
    return p.returncode


if __name__ == "__main__":
    sys.exit(main())
