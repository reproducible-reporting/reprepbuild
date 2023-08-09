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
r"""Recursively flatten a LaTeX file.

The following commands are expanded:

- ``\input``: standard LaTeX command
- ``\warninput``: specialized input used by reprepbuild,
  which prints a warning when a file is missing,
  instead of producing an error.

This script is intentionally somewhat limited.
It expects that the input commands are the only
commands present on the line, to avoid ambiguities.
If this is not the case, the script will fail.

The result is printed to the standard output.
"""


import argparse
import os
import sys


def main():
    """Main program."""
    args = parse_args()
    workdir = os.path.dirname(args.path_tex)
    return flatten_latex(workdir, args.path_tex)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser("rr-latexflat")
    parser.add_argument("path_tex", help="The top-level tex file.")
    return parser.parse_args()


def flatten_latex(workdir, path_tex):
    with open(path_tex) as f:
        for iline, line in enumerate(f):
            stripped = line[: line.find("%")].strip()
            stripped = stripped.replace(" ", "").replace("\t", "")
            for cmd in r"\input{", r"\warninput{":
                sub_path_tex = None
                if cmd in stripped:
                    if stripped.startswith(cmd) and stripped.endswith("}"):
                        sub_path_tex = os.path.join(workdir, stripped[len(cmd) : -1])
                        if not os.path.isfile(sub_path_tex):
                            sub_path_tex += ".tex"
                            if not os.path.isfile(sub_path_tex):
                                raise ValueError(
                                    f"Could not locate input file '{sub_path_tex}' "
                                    f"on line {iline+1} in '{path_tex}'"
                                )
                    else:
                        raise ValueError(
                            f"Could not parse '{stripped}' on line {iline+1} in '{path_tex}'"
                        )
                if sub_path_tex is not None:
                    flatten_latex(workdir, sub_path_tex)
                    break
            else:
                sys.stdout.write(line)


if __name__ == "__main__":
    main()
