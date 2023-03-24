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
r"""List all the (missing) dependencies of a LaTeX source.

This also renames the aux tot bibaux for subsequent bibtex execution.
By renaming, it is not overwritten by later LaTeX runs, which would mark the bbl as outdated.
"""


import argparse
import os
import shutil
import subprocess

from .utils import parse_inputs_fls, write_depfile, write_dyndep


def main():
    """Main program."""
    args = parse_args()
    return run_latex_deps(args.fn_tex)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser("rr-bibtex")
    parser.add_argument("fn_tex", help="The top-level tex file.")
    return parser.parse_args()


def run_latex_deps(fn_tex):
    workdir, filename = os.path.split(fn_tex)
    if not filename.endswith(".tex"):
        print(f"Input must have aux extension. Got {fn_tex}")
        return 2
    prefix = filename[:-4]

    args = ["pdflatex", "-interaction=nonstopmode", "-recorder", "-draftmode", filename]
    subprocess.run(
        args,
        cwd=workdir,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Extract relevant files for log, fls and bbl files.
    inputs = parse_inputs_fls(os.path.join(workdir, prefix + ".fls"))
    # The encoding is unpredictable, so read log as binary.
    fn_log = os.path.join(workdir, prefix + ".log")
    if os.path.isfile(fn_log):
        with open(fn_log, "rb") as f:
            for line in f:
                filename = None
                if line.startswith(b"No file "):
                    filename = line[8:-2]
                elif line.startswith(b"LaTeX Warning: File `") or line.startswith(
                    b"! LaTeX Error: File `"
                ):
                    line = line[21:]
                    filename = line[: line.find(b"'")]
                if filename is not None:
                    inputs.append(os.path.join(workdir, filename.decode("utf8")))

    # Write the dyndep, which is the most complete
    fn_pdf = os.path.join(workdir, f"{prefix}.pdf")
    fn_dd = os.path.join(workdir, f"{prefix}.dd")
    write_dyndep(fn_dd, fn_pdf, [], inputs)

    # Write a depfile for all tex sources, in which changes may affect dependencies.
    fn_depfile = fn_dd + ".depfile"
    write_depfile(fn_depfile, [fn_dd], [path for path in inputs if path.endswith(".tex")])

    # Make a copy of the aux file for bibtex.
    # This copy circumvents one of the annoying LaTeX circular dependencies.
    # Without this trick, LaTeX is incompatible with build systems,
    # because the same files serve as input and output in one build step.
    fn_aux1 = os.path.join(workdir, f"{prefix}.aux")
    fn_aux2 = os.path.join(workdir, f"{prefix}.first.aux")
    shutil.copy(fn_aux1, fn_aux2)


if __name__ == "__main__":
    main()
