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
import sys
from collections import namedtuple
from glob import glob

from ninja.ninja_syntax import Writer

__all__ = ("main",)


DEFAULT_RULES = {
    "latex": {"command": "rr-latex $in", "depfile": "$out.depfile"},
    "copy": {"command": "cp $in $out"},
    "latexdiff": {"command": "latexdiff $in > $out"},
    "reprozip": {"command": "rr-zip $out $in"},
    "reproarticlezip": {"command": "rr-article-zip $out $in", "depfile": "$out.depfile"},
    "svgtopdf": {
        "command": "inkscape $in --export-filename=$out --export-type=pdf; rr-normalize-pdf $out"
    },
    "pythonscript": {"command": "rr-python-script $script", "depfile": "$script.depfile"},
}


def latex_pattern(path):
    result = re.match("latex-(?P<prefix>[a-z]*)/(?P=prefix).tex$", path)
    if not result:
        return
    prefix = result.group("prefix")
    workdir = f"latex-{prefix}"
    return [
        {
            "outputs": f"{workdir}/{prefix}.pdf",
            "rule": "latex",
            "inputs": f"{workdir}/{prefix}.tex",
        },
        {
            "outputs": f"uploads/{prefix}.pdf",
            "rule": "copy",
            "inputs": f"{workdir}/{prefix}.pdf",
        },
    ]


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


def latex_article_pattern(path):
    result = re.match("latex-article/article.tex$", path)
    if not result:
        return
    return [
        {
            "outputs": f"uploads/article.zip",
            "rule": "reproarticlezip",
            "inputs": f"latex-article/article.pdf",
        }
    ]


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

    # Try to call the function reprebbuild_info.
    # If it is not present, the script is ignored.
    spec = importlib.util.spec_from_file_location("<pythonscript>", path)
    pythonscript = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pythonscript)
    if not hasattr(pythonscript, "reprepbuild_info"):
        return

    # Call the function as if the script is running in its own directory.
    orig_workdir = os.getcwd()
    workdir = os.path.dirname(path)
    try:
        os.chdir(workdir)
        info = pythonscript.reprepbuild_info()
    finally:
        os.chdir(orig_workdir)

    # Prepare a build record
    def fixpath(local_path):
        return os.path.normpath(os.path.join(workdir, local_path))

    return [
        {
            "inputs": [fixpath(ipath) for ipath in info["inputs"]] + [path],
            "rule": "pythonscript",
            "outputs": [fixpath(opath) for opath in info["outputs"]],
            "variables": {"script": path},
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
    latex_article_pattern,
    latexdiff_pattern,
    dataset_pattern,
    svg_pattern,
    python_script_pattern,
]


def parse_args():
    parser = argparse.ArgumentParser("rr", "Build the publication")
    parser.add_argument(
        "-n",
        "--dry-run",
        default=False,
        action="store_true",
        help="Generate the build.ninja file and dry-run ninja.",
    )
    return parser.parse_args()


def sanity_check():
    """Is there any latex-* folder?"""
    if len(glob("latex-*/*.tex")) == 0:
        print("Wrong directory? No file matching latex-*/*.tex")
        sys.exit(1)


def main():
    sanity_check()
    args = parse_args()
    write_ninja(DEFAULT_PATTERNS, DEFAULT_RULES)
    if args.dry_run:
        os.system("ninja -nv")
    else:
        os.system("ninja -v")


if __name__ == "__main__":
    main()
