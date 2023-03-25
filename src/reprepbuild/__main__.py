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
"""Main driver for building a manuscript or publication from its sources.

When the package installed, the script rr is the entry point to the main
function below. It ignores any arguments. In the directory where it is
executed, the relative path latex_main/main.tex must exist. It will create a new
file build.ninja (or overwrite an existing one) and then run ninja.

The details of the build process cannot be influenced by command-line arguments.
This is by design, to have only one (reproducible) way to build the publication
from the source, for which all the settings and details are stored in files.
"""

import os
import re
import subprocess
import sys
from glob import glob

from ninja.ninja_syntax import Writer

from .utils import check_script_args, import_python_path

__all__ = ("main",)


DEFAULT_RULES = {
    "latexdep": {"command": "rr-latexdep $in", "depfile": "$in.d"},
    "bibtex": {"command": "rr-bibtex $in", "depfile": "$in.d"},
    "latex": {"command": "rr-latex $in"},
    "copy": {"command": "cp $in $out"},
    "latexdiff": {"command": "latexdiff $in > $out"},
    "reprozip": {"command": "rr-zip $out $in"},
    "reproarticlezip": {"command": "rr-article-zip $out $in"},
    "svgtopdf": {
        "command": "inkscape $in --export-filename=$out --export-type=pdf; rr-normalize-pdf $out"
    },
    "pythonscript": {"command": "rr-python-script $in -- $args > $out", "depfile": "$in.d"},
}


def latex_pattern(path):
    """Make ninja build commands to compile latex with pdflatex."""
    result = re.match("latex-(?P<prefix>[a-z]*)/(?P=prefix).tex$", path)
    if not result:
        return
    prefix = result.group("prefix")
    workdir = f"latex-{prefix}"

    def fixpath(fn_local):
        return os.path.normpath(os.path.join(workdir, fn_local))

    yield {
        "outputs": fixpath(f"{prefix}.tex.dd"),
        "implicit_outputs": [
            fixpath(f"{prefix}.aux"),
            fixpath(f"{prefix}.first.aux"),
            fixpath(f"{prefix}.fls"),
            fixpath(f"{prefix}.log"),
        ],
        "rule": "latexdep",
        "inputs": fixpath(f"{prefix}.tex"),
    }
    yield {
        "outputs": fixpath(f"{prefix}.bbl"),
        "implicit_outputs": fixpath(f"{prefix}.blg"),
        "rule": "bibtex",
        "inputs": fixpath(f"{prefix}.first.aux"),
    }
    yield {
        "outputs": fixpath(f"{prefix}.pdf"),
        "rule": "latex",
        "inputs": fixpath(f"{prefix}.tex"),
        "order_only": fixpath(f"{prefix}.tex.dd"),
        "dyndep": fixpath(f"{prefix}.tex.dd"),
    }
    yield {
        "outputs": os.path.join("uploads", f"{prefix}.pdf"),
        "rule": "copy",
        "inputs": fixpath(f"{prefix}.pdf"),
        "default": True,
    }
    if prefix == "article":
        yield {
            "outputs": os.path.join("uploads", "article.zip"),
            "rule": "reproarticlezip",
            "inputs": "latex-article/article.pdf",
            "default": True,
        }


def latexdiff_pattern(path):
    """Make ninja build commands to generate a latex diff."""
    result = re.match("latex-(?P<prefix>[a-z]*)/(?P=prefix)-old.(?P<ext>.*)$", path)
    if not result:
        return
    prefix = result.group("prefix")
    ext = result.group("ext")
    workdir = f"latex_{prefix}"

    def fixpath(fn_local):
        return os.path.normpath(os.path.join(workdir, fn_local))

    yield {
        "outputs": fixpath(f"{prefix}-diff.{ext}"),
        "rule": "latexdiff",
        "inputs": [fixpath(f"{prefix}-old.{ext}"), fixpath(f"{prefix}.{ext}")],
    }
    if ext == "tex":
        yield {
            "outputs": fixpath(f"{prefix}-diff.pdf"),
            "rule": "latex",
            "inputs": fixpath(f"{prefix}-diff.tex"),
        }
        yield {
            "outputs": os.path.join("uploads", f"{prefix}-diff.pdf"),
            "rule": "copy",
            "inputs": fixpath(f"{prefix}-diff.pdf"),
            "default": True,
        }


def dataset_pattern(path):
    """Make ninja build commands to ZIP datasets."""
    result = re.match("dataset-(?P<name>[a-z-]*)/$", path)
    if not result:
        return
    name = result.group("name")
    yield {
        "outputs": f"uploads/dataset-{name}.zip",
        "rule": "reprozip",
        "inputs": [
            path for path in glob(f"dataset-{name}/**", recursive=True) if not path.endswith("/")
        ],
        "default": True,
    }


def svg_pattern(path):
    """Make ninja build commands to convert SVG to PDF files."""
    result = re.match("(?P<name>[a-z/-]*).svg$", path)
    if not result:
        return
    name = result.group("name")
    yield {
        "outputs": f"{name}.pdf",
        "rule": "svgtopdf",
        "inputs": f"{name}.svg",
        "default": True,
    }


def python_script_pattern(path):
    """Make ninja build commands for python scripts."""
    # for any valid python file
    if not re.match(r"(?P<name>[a-zA-Z0-9/_-]*[a-zA-Z][a-zA-Z0-9_-]*).py$", path):
        return

    # Call reprepbuild_info as if the script is running in its own directory.
    orig_workdir = os.getcwd()
    workdir, fn_py = os.path.split(path)
    prefix = fn_py[:-3]
    try:
        # Load the script in its own directory
        os.chdir(workdir)
        pythonscript = import_python_path(fn_py)

        # Get the relevant functions
        reprepbuild_info = getattr(pythonscript, "reprepbuild_info", None)
        if reprepbuild_info is None:
            return
        reprepbuild_cases = getattr(pythonscript, "reprepbuild_cases", None)
        if reprepbuild_cases is None:
            build_cases = [[]]
        else:
            build_cases = reprepbuild_cases()

        def fixpath(fn_local):
            return os.path.normpath(os.path.join(workdir, fn_local))

        # Loop over all cases to make build records
        for script_args in build_cases:
            build_info = reprepbuild_info(*script_args)
            strargs = check_script_args(script_args)
            fn_log = fixpath(f"{prefix}{strargs}.log")
            yield {
                "inputs": path,
                "implicit": [fixpath(ipath) for ipath in build_info.get("inputs", [])],
                "rule": "pythonscript",
                "implicit_outputs": [fixpath(opath) for opath in build_info.get("outputs", [])],
                "outputs": fn_log,
                "variables": {
                    "args": " ".join(str(arg) for arg in script_args),
                    "strargs": strargs,
                },
                "default": True,
            }
    finally:
        os.chdir(orig_workdir)


def write_ninja(patterns, rules):
    """Search through the source for patterns that can be translated into ninja build commands."""
    # Loop over all files and create rules and builds for them
    rule_names = set()
    builds = []
    defaults = []
    for path in glob("**", recursive=True):
        for pattern in patterns:
            for build in pattern(path):
                if build.get("default", False):
                    defaults.append(build["outputs"])
                    del build["default"]
                rule_names.add(build["rule"])
                builds.append(build)

    # Sanity check
    if len(builds) == 0:
        print("Nothing to build. Wrong current directory?")
        sys.exit(-1)

    # Format rules and builds
    with open("build.ninja", "w") as f:
        writer = Writer(f, 100)
        for rule_name in rule_names:
            writer.rule(name=rule_name, **rules[rule_name])
        for build in builds:
            writer.build(**build)
        for default in defaults:
            writer.default(default)


DEFAULT_PATTERNS = [
    latex_pattern,
    latexdiff_pattern,
    dataset_pattern,
    svg_pattern,
    python_script_pattern,
]


def parse_args():
    """Parse command-line arguments."""
    args = sys.argv[1:]
    if any(arg in ["-?", "-h", "--help"] for arg in args):
        print("All command-line arguments are passed on to the ninja subprocess.")
        print("Run `ninja -h` for details.")
        sys.exit(2)
    return args


def sanity_check():
    """Is there any latex-* folder with tex files?"""
    if len(glob("latex-*/*.tex")) == 0:
        print("Wrong directory? No file matching latex-*/*.tex")
        sys.exit(1)


def main():
    """Main program."""
    sanity_check()
    args = parse_args()
    write_ninja(DEFAULT_PATTERNS, DEFAULT_RULES)
    subprocess.run(["ninja"] + args)


if __name__ == "__main__":
    main()
