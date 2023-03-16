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

import argparse
import importlib
import os
import re
import subprocess
import sys
from collections import namedtuple
from glob import glob

from ninja.ninja_syntax import Writer

__all__ = ("main",)


DEFAULT_RULES = {
    "latex": {"command": "rr-latex $in"},
    "latexdep": {"command": "rr-latex -s $in"},
    "copy": {"command": "cp $in $out"},
    "latexdiff": {"command": "latexdiff $in > $out"},
    "reprozip": {"command": "rr-zip $out $in"},
    "reproarticlezip": {"command": "rr-article-zip $out $in"},
    "svgtopdf": {
        "command": "inkscape $in --export-filename=$out --export-type=pdf; rr-normalize-pdf $out"
    },
    "pythonscript": {"command": "rr-python-script $in", "depfile": "$script.depfile"},
}


def latex_pattern(path):
    result = re.match("latex-(?P<prefix>[a-z]*)/(?P=prefix).tex$", path)
    if not result:
        return
    prefix = result.group("prefix")
    workdir = f"latex-{prefix}"
    builds = [
        {
            "outputs": f"{workdir}/{prefix}.pdf.dd",
            "rule": "latexdep",
            "inputs": f"{workdir}/{prefix}.tex",
        },
        {
            "outputs": f"{workdir}/{prefix}.pdf",
            "rule": "latex",
            "inputs": f"{workdir}/{prefix}.tex",
            "order_only": f"{workdir}/{prefix}.pdf.dd",
            "dyndep": f"{workdir}/{prefix}.pdf.dd",
        },
        {
            "outputs": f"uploads/{prefix}.pdf",
            "rule": "copy",
            "inputs": f"{workdir}/{prefix}.pdf",
        },
    ]
    if prefix == "article":
        builds.append(
            {
                "outputs": f"uploads/article.zip",
                "rule": "reproarticlezip",
                "inputs": f"latex-article/article.pdf",
            }
        )
    return builds


def latexdiff_pattern(path):
    result = re.match("latex-(?P<prefix>[a-z]*)/(?P=prefix)-old.(?P<ext>)$", path)
    if not result:
        return
    prefix = result.group("prefix")
    ext = result.group("ext")
    workdir = f"latex_{prefix}"
    builds = [
        {
            "outputs": f"{workdir}/{prefix}-diff.{ext}",
            "rule": "latexdiff",
            "inputs": f"{workdir}/{prefix}-old.{ext} {workdir}/{prefix}.{ext}",
        }
    ]
    if ext == "tex":
        builds += [
            {
                "outputs": f"{workdir}/{prefix}-diff.pdf",
                "rule": "latex",
                "inputs": f"{workdir}/{prefix}-diff.tex",
            },
            {
                "outputs": f"uploads/{prefix}-diff.pdf",
                "rule": "copy",
                "inputs": f"{workdir}/{prefix}-diff.pdf",
            },
        ]
    return builds


def dataset_pattern(path):
    result = re.match("dataset-(?P<name>[a-z-]*)/$", path)
    if not result:
        return
    name = result.group("name")
    return [
        {
            "outputs": f"uploads/dataset-{name}.zip",
            "rule": "reprozip",
            "inputs": " ".join(
                path
                for path in glob(f"dataset-{name}/**", recursive=True)
                if not path.endswith("/")
            ),
        }
    ]


def svg_pattern(path):
    result = re.match("(?P<name>[a-z/-]*).svg$", path)
    if not result:
        return
    name = result.group("name")
    return [
        {
            "outputs": f"{name}.pdf",
            "rule": "svgtopdf",
            "inputs": f"{name}.svg",
        }
    ]


def python_script_pattern(path):
    if not re.match("(?P<name>[a-z/-]*).py$", path):
        return

    # Call reprepbuild_info as if the script is running in its own directory.
    orig_workdir = os.getcwd()
    workdir, fn_py = os.path.split(path)
    try:
        os.chdir(workdir)
        # Try to call the function reprebbuild_info.
        # If it is not present, the script is ignored.
        spec = importlib.util.spec_from_file_location("<pythonscript>", fn_py)
        pythonscript = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pythonscript)
        reprepbuild_info = getattr(pythonscript, "reprepbuild_info", None)
        if reprepbuild_info is None:
            return
        info = reprepbuild_info()
    finally:
        os.chdir(orig_workdir)

    # Prepare a build record
    def fixpath(local_path):
        return os.path.normpath(os.path.join(workdir, local_path))

    return [
        {
            "inputs": [path],
            "implicit": [fixpath(ipath) for ipath in info["inputs"]],
            "rule": "pythonscript",
            "outputs": [fixpath(opath) for opath in info["outputs"]],
        }
    ]


def write_ninja(patterns, rules):
    # Loop over all files and create rules and builds for them
    rule_names = set()
    builds = []
    for path in glob("**", recursive=True):
        for pattern in patterns:
            result = pattern(path)
            if result is not None:
                for build in result:
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


DEFAULT_PATTERNS = [
    latex_pattern,
    latexdiff_pattern,
    dataset_pattern,
    svg_pattern,
    python_script_pattern,
]


def parse_args():
    args = sys.argv[1:]
    if any(arg in ["-?", "-h", "--help"] for arg in args):
        print("All command-line arguments are passed on to the ninja subprocess.")
        print("Run `ninja -h` for details.")
        sys.exit(2)
    return args


def sanity_check():
    """Is there any latex-* folder?"""
    if len(glob("latex-*/*.tex")) == 0:
        print("Wrong directory? No file matching latex-*/*.tex")
        sys.exit(1)


def main():
    sanity_check()
    args = parse_args()
    write_ninja(DEFAULT_PATTERNS, DEFAULT_RULES)
    subprocess.run(["ninja"] + args)


if __name__ == "__main__":
    main()
