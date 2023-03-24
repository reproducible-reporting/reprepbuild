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
"""Run BibTex on a LaTeX aux file."""


import argparse
import os
import subprocess

from .utils import write_depfile


def main():
    """Main program."""
    args = parse_args()
    return run_bibtex(args.fn_aux)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser("rr-bibtex")
    parser.add_argument("fn_aux", help="The top-level aux file.")
    return parser.parse_args()


def run_bibtex(fn_aux):
    workdir, filename = os.path.split(fn_aux)
    if not filename.endswith(".aux"):
        print(f"Input must have aux extension. Got {fn_aux}")
        return 2
    prefix = filename[:-4]

    args = ["bibtex", filename]
    fn_blg = os.path.join(workdir, prefix + ".blg")
    result = 0
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
        result = 1

    # Parse the blg file to get a list of used bib files
    fns_bib = set()
    with open(fn_blg) as f:
        for line in f:
            if line.startswith("Database file #"):
                fns_bib.add(os.path.join(workdir, line.split()[-1]))

    fn_fls = os.path.join(workdir, prefix + ".fls")
    with open(fn_fls) as f:
        for line in f:
            if line.startswith("OUTPUT "):
                fns_bib.discard(os.path.join(workdir, os.path.normpath(line[7:].strip())))

    if len(fns_bib) == 0:
        result = 0
    if result == 1:
        print(f"    Error running `bibtex {filename}` in `{workdir}`.")
        with open(fn_blg) as f:
            for line in f:
                print(line[:-1])
                if line.startswith("You've used "):
                    break
    else:
        # Store the input bib files for dependency tracking
        fn_bbl = os.path.join(workdir, prefix + ".bbl")
        fn_depfile = fn_bbl + ".depfile"
        write_depfile(fn_depfile, [fn_bbl], fns_bib)

    return result


if __name__ == "__main__":
    main()