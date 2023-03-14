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

from .utils import write_depfile


def main():
    """Main program."""
    compile_tex(parse_args().fn_tex)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser("rr-latex")
    parser.add_argument("fn_tex", help="The top-level tex file.")
    return parser.parse_args()


def compile_tex(fn_tex):
    """Compile the tex file with minimal output."""
    workdir, filename = os.path.split(fn_tex)
    if not filename.endswith(".tex"):
        print(f"Source must have tex extension. Got {workdir}/{filename}")
        sys.exit(2)
    prefix = filename[:-4]

    if os.environ.get("SOURCE_DATE_EPOCH") != "0":
        print("SOURCE_DATE_EPOCH is not set to 0.")
        sys.exit(1)

    # Compile the LaTeX source with latexmk
    try:
        with open(os.path.join(workdir, prefix + ".latexmk"), "w") as f:
            subprocess.run(
                ["latexmk", "-pdf", "-g", prefix],
                cwd=workdir,
                check=True,
                stdin=subprocess.DEVNULL,
                stdout=f,
                stderr=f,
            )
    except subprocess.CalledProcessError:
        # Print minimal output explaining the error, if possible.
        fn_log = os.path.join(workdir, prefix + ".log")
        found_error = False
        fn_source = "<unknown source>"
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
        sys.exit(1)

    # Convert the fls file into a depfile
    inputs = []
    with open(os.path.join(workdir, prefix + ".fls")) as f:
        for line in f:
            if line.startswith("INPUT "):
                ipath = line[6:].strip()
                ipath = os.path.normpath(ipath)
                ipath = os.path.join(workdir, ipath)
                inputs.append(ipath)

    fn_pdf = os.path.join(workdir, prefix + ".pdf")
    fn_depfile = os.path.join(workdir, prefix + ".pdf.depfile")
    write_depfile(fn_depfile, [fn_pdf], inputs)


if __name__ == "__main__":
    main()
