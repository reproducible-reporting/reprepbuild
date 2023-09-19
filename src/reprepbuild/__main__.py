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

When the package is installed, the script ``rr`` is the entry point to the main function below.
The script creates a ``ninja.build`` file and then calls ``ninja``, passing all arguments.
In the directory where it is executed, there must be a ``reprepbuild.yaml`` file,
which configures the build process.

The details of the build process cannot be influenced by command-line arguments.
This is by design, to have only one (reproducible) way to build a publication
from the source, for which all the settings and details are stored in files.
"""

import os
import subprocess
import sys

from ninja import Writer

from .config import load_config

__all__ = ("main", "generator")


def generator(root: str):
    """Parse ``reprebuild.yaml`` files and write a ``build.ninja`` file.

    Parameters
    ----------
    root
        Directory where to start, i.e. where the top-level ``reprebuild.yaml`` is located.
    """
    # Parse the reprepbuild.yaml files (recursively)
    tasks = []
    load_config(os.getcwd(), "reprepbuild.yaml", tasks)

    # Loop over all files and create rules and builds for them.
    with open("build.ninja", "w") as f:
        writer = Writer(f, 100)

        # Write all rules, even if some are not used.
        writer.comment("All rules")
        rules = {}
        for task in tasks:
            for rule_name, rule in task.command.rules.items():
                if rule_name in rules:
                    if rules[rule_name] != rule:
                        raise ValueError(f"Same name but different rules: {rule_name}")
                else:
                    rules[rule_name] = rule
                    mkdir_rule = rule.copy()
                    mkdir_rule["command"] = "mkdir -p ${dstdirs} && " + rule["command"]
                    rules[rule_name + "_mkdir"] = mkdir_rule
        for rule_name, rule in rules.items():
            writer.rule(name=rule_name, **rule)
        writer.newline()

        # Write all build lines with comments and defaults
        outputs = set()
        not_scanned = set()
        for task in tasks:
            for records, new_not_scanned in task.generate(outputs):
                not_scanned.update(new_not_scanned)
                for record in records:
                    if isinstance(record, str):
                        writer.comment(record)
                    elif isinstance(record, list):
                        writer.default(record)
                    elif isinstance(record, dict):
                        writer.build(**record)
                        outputs.update(record["outputs"])
                        outputs.update(record.get("implicit_outputs", []))
                    else:
                        raise TypeError("Cannot process ")
                writer.newline()

        # Insert generator if some files could not be scanned
        if len(not_scanned) > 0:
            writer.newline()
            writer.comment("Some dependencies were absent, which could induce additional builds.")
            writer.comment("This means the build.ninja file needs to be regenerated.")
            writer.rule("generator", command="rr-generator .", generator=True)
            writer.build(rule="generator", implicit=sorted(not_scanned), outputs="build.ninja")


def parse_args():
    """Parse command-line arguments."""
    args = sys.argv[1:]
    if any(arg in ["-?", "-h", "--help"] for arg in args):
        print("All command-line arguments are passed on to the ninja subprocess.")
        print("Run `ninja -h` for details.")
        sys.exit(2)
    return args


def sanity_check():
    """Is there any reprepbuild.yaml file?"""
    if not os.path.exists("reprepbuild.yaml"):
        print("Wrong directory? File reprepbuild.yaml not found.")
        sys.exit(1)


def main():
    """Main program."""
    sanity_check()
    args = parse_args()
    generator(os.getcwd())
    subprocess.run(["ninja", *args], check=False)


if __name__ == "__main__":
    main()
