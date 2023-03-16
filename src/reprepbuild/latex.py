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
r"""Compile a reproducible PDF from a latex source.

To make reproducibility work, put the following in your tex source:

% Make PDFLaTeX builds reproducible
\pdfinfoomitdate=1
\pdfsuppressptexinfo=-1
\pdftrailerid{}
\pdfinfo{/Producer()/Creator()}

The following environment variable must also be set:

export SOURCE_DATE_EPOCH=0

See https://tex.stackexchange.com/questions/229605/reproducible-latex-builds-compile-to-a-file-which-always-hashes-to-the-same-va

"""

import argparse
import os
import subprocess
import sys

from .utils import write_dyndep


def main():
    """Main program."""
    args = parse_args()
    return compile_latex(args.fn_tex, args.silent_fail)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser("rr-latex")
    parser.add_argument("fn_tex", help="The top-level tex file.")
    parser.add_argument(
        "-s",
        "--silent-fail",
        default=False,
        action="store_true",
        help="Do not complain when latex fails.",
    )
    return parser.parse_args()


def compile_latex(fn_tex, silent_fail=False):
    """Compile the tex file with minimal output."""
    workdir, filename = os.path.split(fn_tex)
    if not filename.endswith(".tex"):
        print(f"Source must have tex extension. Got {workdir}/{filename}")
        sys.exit(2)
    prefix = filename[:-4]

    # Check whether we're already in the eighties. (compatibility with ZIP)
    if os.environ.get("SOURCE_DATE_EPOCH") != "315532800":
        print("SOURCE_DATE_EPOCH is not set to 315532800.")
        sys.exit(1)

    # Compile the LaTeX source with latexmk
    fn_log = os.path.join(workdir, prefix + ".log")
    result = 0
    try:
        args = [
            "latexmk",
            "-pdf",
            "-pdflatex=pdflatex -interaction=batchmode -file-line-error",
            "-g",
            prefix,
        ]
        with open(os.path.join(workdir, prefix + ".latexmk"), "w") as f:
            subprocess.run(
                args,
                cwd=workdir,
                check=True,
                stdin=subprocess.DEVNULL,
                stdout=f,
                stderr=f,
            )
    except subprocess.CalledProcessError:
        # Say what was tried.
        if not silent_fail:
            print("    Command failed:", args)

        # Print minimal output explaining the error, if possible.
        found_error = False
        fn_source = "<unknown source>"
        if os.path.isfile(fn_log):
            with open(fn_log) as f:
                for line in f:
                    if line.startswith("**"):
                        fn_source = line[2:-1]
                    if line.startswith("!"):
                        found_error = True
                        break
                if found_error:
                    print("   ", fn_source)
                    print("   ", line[:-1])
                    for line, _ in zip(f, range(2)):
                        print("   ", line[:-1])
            print(f"    See {fn_log} for more details.")
        else:
            print(f"    File {fn_log} was not created.")
        result = 0 if silent_fail else -1

    # Convert the log and fls files into a depfile
    inputs = []
    if os.path.isfile(fn_log):
        with open(fn_log) as f:
            for line in f:
                if line.startswith("LaTeX Warning: File `"):
                    line = line[21:]
                    line = line[: line.find("'")]
                    inputs.append(os.path.join(workdir, line))
    fn_fls = os.path.join(workdir, prefix + ".fls")
    if os.path.isfile(fn_fls):
        with open(fn_fls) as f:
            for line in f:
                if line.startswith("INPUT "):
                    line = line[6:].strip()
                    inputs.append(os.path.join(workdir, line))

    fn_pdf = os.path.join(workdir, prefix + ".pdf")
    fn_dd = os.path.join(workdir, prefix + ".pdf.dd")
    write_dyndep(fn_dd, fn_pdf, [], inputs)
    return result


if __name__ == "__main__":
    main()
