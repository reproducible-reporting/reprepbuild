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
from .generator import BaseGenerator, BuildGenerator

__all__ = ("main", "generate")


def generate(root: str):
    """Parse ``reprebuild.yaml`` files and write a ``build.ninja`` file.

    Parameters
    ----------
    root
        Directory where to start, i.e. where the top-level ``reprebuild.yaml`` is located.
    """
    # Parse the reprepbuild.yaml files (recursively)
    generators = []
    load_config(root, "reprepbuild.yaml", generators)

    # Loop over all files and create pools, rules and builds for them.
    with open("build.ninja", "w") as f:
        writer = Writer(f, 100)

        # Write pools
        pools = _collect_dicts(generators, "pools")
        writer.comment("All pools")
        for pool_name, pool in pools.items():
            writer.pool(name=pool_name, **pool)
        writer.newline()

        # Write all rules, even if some are not used.
        rules = _collect_dicts(generators, "rules")
        writer.comment("All rules (except generator)")
        for rule_name, rule in rules.items():
            writer.rule(name=rule_name, **rule)
        writer.newline()
        writer.comment("All rules with mkdir (except generator)")
        for rule_name, rule in rules.items():
            rule["command"] = "mkdir -p ${dstdirs} && " + rule["command"]
            writer.rule(name=rule_name + "_mkdir", **rule)
        writer.newline()

        # Write all build lines with comments and defaults
        outputs = set()
        defaults = set()
        gendeps = set()
        for generator in generators:
            for records, new_gendeps in generator(outputs, defaults):
                gendeps.update(new_gendeps)
                for record in records:
                    if isinstance(record, str):
                        writer.comment(record)
                    elif isinstance(record, list):
                        for default in record:
                            if default not in defaults:
                                writer.default(record)
                                defaults.update(record)
                    elif isinstance(record, dict):
                        new_outputs = set(record["outputs"])
                        new_outputs |= set(record.get("implicit_outputs", []))
                        if outputs.isdisjoint(new_outputs):
                            writer.build(**record)
                            outputs.update(new_outputs)
                        else:
                            # Some outputs are repeated, in which case no new build lines are
                            # written. It is assumed that the preceding builds are more specific
                            # and therefore should take priority over later ones.
                            # To maintain sanity, ambiguous cases are not allowed, i.e. all
                            # new outputs should already exist.
                            if not new_outputs.issubset(outputs):
                                raise ValueError(
                                    "Outputs are partially generated in previous builds. "
                                    f"New: {new_outputs - outputs} "
                                    f"Existing: {new_outputs & outputs}"
                                )
                            writer.comment("Skipping due to overlap with previous builds.")
                    else:
                        raise TypeError("Cannot process ")
                writer.newline()

        # Insert generator if some files could not be scanned
        if len(gendeps) > 0:
            writer.newline()
            writer.comment("Some files influence the generation of the build files.")
            writer.comment("When they change, the build.ninja file must be regenerated.")
            writer.rule("generator", command="rr-generator .", generator=True)
            writer.build(rule="generator", implicit=sorted(gendeps), outputs="build.ninja")


def _collect_dicts(generators: list[BaseGenerator], attr_name: str) -> dict[str:object]:
    """Combine dictionaries, used for pools and rules."""
    result = {}
    for generator in generators:
        if isinstance(generator, BuildGenerator):
            for name, kwargs in getattr(generator.command, attr_name).items():
                if name in result:
                    if result[name] != kwargs:
                        raise ValueError(f"Same name but different {attr_name}: {name}")
                else:
                    result[name] = kwargs
    return result


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
    generate(os.getcwd())
    subprocess.run(
        ["ninja", *args],
        check=False,
        env=os.environ | {"NINJA_STATUS": "\033[1;36;40m[%f/%t]\033[0;0m "},
    )


if __name__ == "__main__":
    main()
