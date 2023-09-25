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
r"""Print the error message from a LaTeX log file."""

import argparse
import os
import subprocess
import sys
from typing import TextIO

import attrs


@attrs.define
class ErrorInfo:
    program: str = attrs.field(validator=attrs.validators.instance_of(str))
    src: (str | None) = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(str)),
    )
    message: (str | None) = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(str)),
    )

    def print(self, log: str | None = None):
        print(f"\033[1;31;40m{self.program} ERROR\033[0;0m")
        if log is not None:
            print(f"\033[1;35;40mLog file:\033[0;0m {log}")
        if self.src is not None:
            print(f"\033[1;35;40mSource file:\033[0;0m {self.src}")
        if self.message is not None:
            print(self.message)


DEFAULT_MESSAGE = """\
The error message could not be isolated from the log file.
You can open the log file in a text editor and manually locate the error.

Please open a new issue with the log file attached,
which will help improve the script to detect the error message:
https://github.com/reproducible-reporting/reprepbuild/issues

Thank you very much!
"""


def main() -> int:
    """Main program."""
    args = parse_args()

    workdir, fn_tex = os.path.split(args.path_tex)
    workdir = os.path.normpath(workdir)
    if not fn_tex.endswith(".tex"):
        raise ValueError("The LaTeX source must have extension .tex")
    stem = fn_tex[:-4]

    if args.bibtex is not None:
        # LaTeX
        cp = subprocess.run(
            [f"{args.latex}", "-recorder", "-interaction=batchmode", "-draftmode", stem],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            cwd=workdir,
            env=os.environ | {"SOURCE_DATE_EPOCH": "315532800"},
        )
        if cp.returncode != 0:
            path_log = os.path.join(workdir, f"{stem}.log")
            with open(path_log) as fh:
                _, error_info = parse_latex_log(fh)
            error_info.print(path_log)
            return 1

        # BibTeX
        cp = subprocess.run(
            [f"{args.bibtex}", stem],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            cwd=workdir,
            env=os.environ | {"SOURCE_DATE_EPOCH": "315532800"},
        )
        if cp.returncode != 0:
            path_blg = os.path.join(workdir, f"{stem}.blg")
            with open(path_blg) as fh:
                error_info = parse_bibtex_log(fh)
            error_info.print(path_blg)
            return 2

        # BibSane
        if not (args.bibsane is None or args.bibsane == ""):
            bibsane_config = os.path.relpath(args.bibsane_config, workdir)
            cp = subprocess.run(
                ["bibsane", f"{stem}.aux", "--config=" + bibsane_config],
                cwd=workdir,
                text=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            if cp.returncode != 0:
                error_info = ErrorInfo("BibSane", src=f"{workdir}/{stem}.aux")
                error_info.print()
                sys.stdout.write(cp.stdout)
                return 3

    while True:
        # LaTeX
        cp = subprocess.run(
            [f"{args.latex}", "-recorder", "-interaction=batchmode", stem],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            cwd=workdir,
            env=os.environ | {"SOURCE_DATE_EPOCH": "315532800"},
        )
        path_log = os.path.join(workdir, f"{stem}.log")
        with open(path_log) as fh:
            recompile, error_info = parse_latex_log(fh)
        if cp.returncode != 0:
            error_info.print(path_log)
            return 4
        if not recompile:
            return 0


def parse_latex_log(fh: TextIO) -> tuple[bool, (ErrorInfo | None)]:
    """Parse a LaTeX log file.

    Parameters
    ----------
    fh
        The opened log file

    Returns
    -------
    recompile
        ``True`` if the source needs to be recompiled.
    error_info
        Structured info for printing error, or None
    """
    last_src = "(could not detect source file)"
    error = False
    recompile = False
    num_empty = 0
    recorded = []
    for line in fh.readlines():
        if error:
            recorded.append(line.strip())
            if recorded[-1] == "":
                num_empty += 1
            if num_empty == 2:
                break
        elif line.startswith("("):
            last_file = line[1:].strip()
            if not ("(" in last_file or ")" in last_file or last_file.startswith("/")):
                last_src = last_file
                continue
        elif line.startswith("!"):
            error = True
            recorded.append(line[:-1])
        elif "Rerun to get cross-references right." in line:
            recompile = True
            break

    message = "\n".join(recorded) if error else DEFAULT_MESSAGE
    return recompile, ErrorInfo("LaTeX", last_src, message=message)


def parse_bibtex_log(fh: TextIO) -> ErrorInfo | None:
    """Parse a BibTeX log file.

    Parameters
    ----------
    fh
        The opened blg file

    Returns
    -------
    error_info
        Structured info for printing error, or None
    """
    last_src = "(could not detect source file)"
    error = False
    recorded = []
    for line in fh.readlines():
        if line.startswith("Database file #"):
            last_src = line[line.find(":") + 1 :].strip()
            recorded = []
        else:
            recorded.append(line[:-1])
        if line == "I'm skipping whatever remains of this entry\n":
            error = True
            break

    message = "\n".join(recorded) if error else DEFAULT_MESSAGE
    return ErrorInfo("BibTeX", last_src, message=message)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        "rr-latex",
        description="Compile a LaTeX document and print essence from log file.",
    )
    parser.add_argument("path_tex", help="The main LaTeX source file.")
    parser.add_argument("latex", help="The LaTeX executable.")
    parser.add_argument(
        "--bibtex",
        default=None,
        help="BibTeX executable to use on the source. BibTeX is not used when not given.",
    )
    parser.add_argument(
        "--bibsane",
        default=None,
        help="BibSane executable to use on the source. BibSane is not used when not given.",
    )
    parser.add_argument(
        "--bibsane-config",
        default="bibsane.yaml",
        help="BibSane configuration file. default=%(default)s",
    )
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
