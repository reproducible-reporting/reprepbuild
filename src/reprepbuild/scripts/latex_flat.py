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
r"""Recursively flatten a LaTeX file.

The following commands are expanded:

- ``\input``: standard LaTeX command
- ``\import``: like ``\input``, but capable of handling directory changes.

The following commands are rewritten to be consistent with the location of the flattened output:

- ``\includegraphics``
- ``\thebibliography``

This script is intentionally somewhat limited.
It expects that ``\input`` and ``\import`` commands are the only ones present on their line,
to avoid ambiguities. If this is not the case, the script will fail.
The script als assumes the ``\includgraphics`` and ``\thebibliography``
commands are contained within a single line.
"""


import argparse
import os
import re
import sys
from typing import TextIO


def main() -> int:
    """Main program."""
    args = parse_args()
    with open(args.path_flat, "w") as fh_out:
        out_root = os.path.normpath(os.path.dirname(args.path_flat))
        return flatten_latex(args.path_tex, fh_out, out_root)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="rr-latex-flat",
        description="Flatten input and import commands in a LaTeX file.",
    )
    parser.add_argument("path_tex", help="The top-level tex file.")
    parser.add_argument("path_flat", help="The flattened output tex file.")
    return parser.parse_args()


def flatten_latex(path_tex: str, fh_out: TextIO, out_root: str, tex_root: str | None = None) -> int:
    """Write a flattened LaTeX file

    Parameters
    ----------
    path_tex
        The LaTeX source to be flattened, may be the main file or
        an included file in one of the recursions.
    fh_out
        The file object to write the flattened file to.
    out_root
        The directory of the output file, needed to fix relative paths.
    tex_root
        The directory with respect to which paths in the LaTeX source must
        be interpreted.
    """
    if tex_root is None:
        tex_root = os.path.normpath(os.path.dirname(path_tex))
    with open(path_tex) as f:
        for iline, line in enumerate(f):
            # Reduce line to standard form
            stripped = line[: line.find("%")].strip()
            stripped = stripped.replace(" ", "").replace("\t", "")

            # Try to find input or import
            status = 0
            sub_path_tex = None
            new_root = tex_root
            if r"\input{" in stripped:
                if stripped.startswith(r"\input{") and stripped.endswith("}"):
                    sub_path_tex = os.path.join(tex_root, stripped[7:-1])
                    if not os.path.isfile(sub_path_tex):
                        sub_path_tex += ".tex"
                        if not os.path.isfile(sub_path_tex):
                            status = -1
                else:
                    status = -2
            elif r"\import{" in stripped:
                if stripped.startswith(r"\import{") and "}{" in stripped and stripped.endswith("}"):
                    new_root, sub_path_tex = stripped[8:-1].split("}{")
                    new_root = os.path.normpath(os.path.join(tex_root, new_root))
                    sub_path_tex = os.path.join(new_root, sub_path_tex)
                    if not os.path.isfile(sub_path_tex):
                        sub_path_tex += ".tex"
                        if not os.path.isfile(sub_path_tex):
                            status = -1
                else:
                    status = -2

            # Handle result
            if status < 0:
                if status == -1:
                    print(
                        f"Could not locate input file '{sub_path_tex}' "
                        f"on line {iline+1} in '{path_tex}'"
                    )
                elif status == -2:
                    print(f"Could not parse '{stripped}' on line {iline+1} in '{path_tex}'")
                else:
                    print("Unknown error")
                return status
            elif isinstance(sub_path_tex, str):
                flatten_latex(sub_path_tex, fh_out, out_root, new_root)
            else:
                fh_out.write(rewrite_line(line, tex_root, out_root))
    return 0


RE_REWRITE = re.compile(
    r"(?P<comopt>\\(?:includegraphics|thebibliography)(?:\s*\[.*?])?\s*)\{(?P<path>.*?)}"
)


def rewrite_line(line, tex_root, out_root):
    """Rewrite the path in a source line.

    Parameters
    ----------
    line
        A line of LaTeX source code, possibly containing ``\\includegraphics``
        or ``\\thebibliography`` commands that need fixing.
    tex_root
        The directory with respect to which paths in the LaTeX source should
        be interpreted.
    out_root
        The new directory, with respect to which paths in the rewritten
        LaTeX source must be interpreted.

    Returns
    -------
    fixed_line
        A line in which the paths are fixed.
    """

    def repl(m):
        old_path = m.group("path")
        new_path = os.path.normpath(os.path.relpath(os.path.join(tex_root, old_path), out_root))
        return m.group("comopt") + "{" + new_path + "}"

    return RE_REWRITE.sub(repl, line)


if __name__ == "__main__":
    sys.exit(main())
