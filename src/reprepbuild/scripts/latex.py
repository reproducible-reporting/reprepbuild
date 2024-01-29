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
r"""Print the error message from a LaTeX log file."""

import argparse
import os
import re
import subprocess
import sys

import attrs

from .manifest import compute_sha256


@attrs.define
class ErrorInfo:
    program: str = attrs.field(validator=attrs.validators.instance_of(str))
    src: str | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(str)),
    )
    message: str | None = attrs.field(
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
> The error message could not be isolated from the file {path}.
> You can open the file {path} in a text editor and locate the error manually.
>
> Please open a new issue with the file {path} attached,
> which will help improve the script to detect the error message:
> https://github.com/reproducible-reporting/reprepbuild/issues
>
> Thank you very much!
"""

MESSAGE_SUFFIX = """
> If the above extract from the log file can be improved,
> open a new issue with the file {path} attached:
> https://github.com/reproducible-reporting/reprepbuild/issues
"""


def main() -> int:
    """Main program."""
    args = parse_args()

    workdir, fn_tex = os.path.split(args.path_tex)
    workdir = os.path.normpath(workdir)
    if not fn_tex.endswith(".tex"):
        raise ValueError("The LaTeX source must have extension .tex")
    stem = fn_tex[:-4]
    path_aux = os.path.join(workdir, f"{stem}.aux")

    # Remove existing outputs from a previous run, which could potentially
    # conflict with the new tex source files. In 99% of the cases, this is
    # not a problem, but sometimes LaTeX chokes on remnants in old outputs.
    exts_to_remove = ["log", "aux", "blg", "fls", "out", "toc", "nlo", "synctex"]
    if args.bibtex is not None:
        exts_to_remove.append("bbl")
    for ext in exts_to_remove:
        path_to_remove = os.path.join(workdir, f"{stem}.{ext}")
        if os.path.isfile(path_to_remove):
            os.remove(path_to_remove)

    aux_sha256_hist = []
    if args.bibtex is not None:
        # LaTeX
        cp = subprocess.run(
            [f"{args.latex}", "-recorder", "-interaction=errorstopmode", "-draftmode", stem],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            cwd=workdir,
            env=os.environ | {"SOURCE_DATE_EPOCH": "315532800"},
        )
        if cp.returncode != 0:
            path_log = os.path.join(workdir, f"{stem}.log")
            _, error_info = parse_latex_log(path_log)
            error_info.print(path_log)
            return 1

        aux_sha256_hist.append(compute_sha256(path_aux)[1])

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
            error_info = parse_bibtex_log(path_blg)
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

    for _ in range(args.maxrep):
        # LaTeX
        cp = subprocess.run(
            [f"{args.latex}", "-recorder", "-interaction=errorstopmode", stem],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            cwd=workdir,
            env=os.environ | {"SOURCE_DATE_EPOCH": "315532800"},
        )
        path_log = os.path.join(workdir, f"{stem}.log")
        error_info = parse_latex_log(path_log)
        if cp.returncode != 0:
            error_info.print(path_log)
            return 4
        aux_sha256_hist.append(compute_sha256(path_aux)[1])
        if len(aux_sha256_hist) > 1 and aux_sha256_hist[-1] == aux_sha256_hist[-2]:
            return 0

    print(f"\033[1;31;40mAux file did not converge in {args.maxrep} iterations!\033[0;0m")
    print(path_aux)
    print("\n".join(aux_sha256_hist))
    return -3


@attrs.define
class LatexSourceStack:
    stack: list[str] = attrs.field(init=False, default=attrs.Factory(list))
    unfinished: str | None = attrs.field(init=False, default=None)
    unmatched: bool = attrs.field(init=False, default=False)

    @property
    def current(self) -> str:
        """The current file to which the error message belongs."""
        if len(self.stack) == 0:
            return "(could not detect source file)"
        else:
            return self.stack[-1]

    def feed(self, line: str):
        # Check if we need to anticipate line wrapping
        full = len(line) == 80
        if full:
            # Some exceptions: guess when 80-char lines end exactly with a filename.
            # This is fragile, but LaTeX log files are just a mess to parse.
            for end in ".tex\n", ".sty\n", ".cls\n", ".def\n", ".cfg\n", ".clo\n":
                if line.endswith(end):
                    full = False
                    break

        # Continue from previous line if needed
        if self.unfinished is not None:
            line = self.unfinished + line
            self.unfinished = None

        if full:
            self.unfinished = line[:-1]
            return

        # Update to stack
        brackets = re.findall(r"\((?:(?:\./|\.\./|/)[-_./a-zA-Z0-9]+)?|\)", line)
        for bracket in brackets:
            if bracket == ")":
                if len(self.stack) == 0:
                    self.unmatched = True
                else:
                    del self.stack[-1]
            else:
                assert bracket.startswith("(")
                self.stack.append(bracket[1:])


def parse_latex_log(path_log: str) -> tuple[bool, (ErrorInfo | None)]:
    """Parse a LaTeX log file.

    Parameters
    ----------
    path_log
        The log file

    Returns
    -------
    error_info
        Structured info for printing error, or None
    """
    lss = LatexSourceStack()
    src = "(could not detect source file)"
    record = False
    found_line = False
    recorded = []

    # LaTeX log files may have encoding errors, so such errors must be ignored.
    with open(path_log, errors="ignore") as fh:
        for line in fh.readlines():
            if record:
                recorded.append(line.rstrip())
                if recorded[-1].strip() == "":
                    record = False
                    if found_line:
                        break
            if line.startswith("!"):
                if not record:
                    recorded.append(line.rstrip())
                record = True
                src = lss.current
            elif line.startswith("l."):
                if not record:
                    recorded.append(line.rstrip())
                record = True
                found_line = True
            else:
                lss.feed(line)

    if len(recorded) > 0:
        message = "\n".join(recorded) + MESSAGE_SUFFIX.format(path=path_log)
    else:
        message = DEFAULT_MESSAGE.format(path=path_log)
    if lss.unmatched:
        message += "> [warning: unmatched closing parenthesis]\n"
    return ErrorInfo("LaTeX", src, message=message)


def update_last_src(line, last_src):
    if not ("(" in line or ")" in line or line.startswith("/")):
        last_src = line
    return last_src


def parse_bibtex_log(path_blg: str) -> ErrorInfo | None:
    """Parse a BibTeX log file.

    Parameters
    ----------
    path_blg
        The blg file.

    Returns
    -------
    error_info
        Structured info for printing error, or None
    """
    last_src = "(could not detect source file)"
    error = False
    recorded = []
    with open(path_blg, errors="ignore") as fh:
        for line in fh.readlines():
            if "---" in line and "file " in line:
                last_src = line.rsplit(maxsplit=1)[-1]
                recorded = []
            recorded.append(line[:-1])
            if line.startswith("I'm skipping whatever remains"):
                error = True
                break
            elif line.startswith(r"I found no \bibstyle command"):
                last_src = line.split()[-1]
                recorded = [line[:-1]]
                error = True
                break

    message = "\n".join(recorded) if error else DEFAULT_MESSAGE.format(path=path_blg)
    return ErrorInfo("BibTeX", last_src, message=message)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="rr-latex",
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
    parser.add_argument(
        "-m",
        "--maxrep",
        default=5,
        type=int,
        help="The maximum number of LaTeX recompilations (not including the one for BibTeX).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
