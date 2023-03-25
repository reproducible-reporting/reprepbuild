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
r"""Compile a reproducible PDF from a latex source, and repeat until converged.

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
import re
import subprocess
import sys


def main():
    """Main program."""
    args = parse_args()
    return compile_latex(args.path_tex)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser("rr-latex")
    parser.add_argument("path_tex", help="The top-level tex file.")
    return parser.parse_args()


def compile_latex(path_tex):
    """Compile the tex file with minimal output."""
    if not path_tex.endswith(".tex"):
        print(f"LaTeX source must have a `.tex` extension. Got {path_tex}")
        return 2
    workdir, fn_tex = os.path.split(path_tex)
    prefix = fn_tex[:-4]

    # Check whether we're already in the eighties. (compatibility with ZIP)
    if os.environ.get("SOURCE_DATE_EPOCH") != "315532800":
        print("SOURCE_DATE_EPOCH is not set to 315532800.")
        return 3

    # Compile the LaTeX source with pdflatex, until converged, max three times
    args = ["pdflatex", "-interaction=nonstopmode", "-recorder", "-file-line-error", fn_tex]
    path_log = os.path.join(workdir, prefix + ".log")
    for irep in range(4):
        found_error = False
        rerun = False
        try:
            subprocess.run(
                args,
                cwd=workdir,
                check=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            # Say what was tried.
            print(f"    Error running `pdflatex {fn_tex}` in `{workdir}`")
            # Print minimal output explaining the error, if possible.

        # Process the log file
        if os.path.isfile(path_log):
            # The encoding is unpredictable, so read as binary.
            with open(path_log, "rb") as f:
                for line in f:
                    if re.match(rb".*\.tex:[0-9]+: ", line) is not None:
                        found_error = True
                        break
                    if b"Rerun to" in line:
                        rerun = True
                        break
                if found_error:
                    # stdout tricks to dump the raw contents on the terminal.
                    sys.stdout.flush()
                    sys.stdout.buffer.write(b"        " + line)
                    for line, _ in zip(f, range(4)):
                        sys.stdout.buffer.write(b"        " + line)
                    print(f"    See {path_log} for more details.")
                    return 1

        if not rerun:
            break


if __name__ == "__main__":
    main()
