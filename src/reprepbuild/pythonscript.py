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
r"""Execute the main function of a Python script.

Reproducible matplotlib figures:
https://matplotlib.org/stable/users/prev_whats_new/whats_new_2.1.0.html#reproducible-ps-pdf-and-svg-output

This script checks whether SOURCE_DATE_EPOCH is 0.

"""

import argparse
import os
import sys

from .utils import check_script_args, import_python_path, write_dep


def main():
    """Main program."""
    args = parse_args()
    script_args = [convert(script_arg) for script_arg in args.script_args]
    return run_script(args.path_py, script_args)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser("rr-python-script")
    parser.add_argument("path_py", help="The python script whose main function will be executed.")
    parser.add_argument(
        "script_args", nargs="*", help="Command-line arguments for the script, if any"
    )
    return parser.parse_args()


def convert(script_arg):
    """Try to convert to int, then float, fallback to string."""
    for dtype in int, float:
        try:
            return dtype(script_arg)
        except ValueError:
            pass
    return script_arg


def run_script(path_py, script_args):
    """Run the python script and collected module dependencies."""
    if not path_py.endswith(".py"):
        print(f"Python script must have `.py` extension. Got {path_py}")
        return 2
    workdir, fn_py = os.path.split(path_py)
    prefix = fn_py[:-3]
    orig_workdir = os.getcwd()

    # Check whether we're already in the eighties. (compatibility with ZIP)
    if os.environ.get("SOURCE_DATE_EPOCH") != "315532800":
        print("SOURCE_DATE_EPOCH is not set to 315532800.")
        return -3

    try:
        # Load the script in its own directory
        os.chdir(workdir)
        pythonscript = import_python_path(fn_py)

        # Get the relevant functions
        reprepbuild_info = getattr(pythonscript, "reprepbuild_info", None)
        if reprepbuild_info is None:
            print(f"The script {path_py} has no reprepbuild_info function.")
            return -1
        script_main = getattr(pythonscript, "main", None)
        if script_main is None:
            print(f"The script {path_py} has no main function.")
            return -1

        # Execute the functions as if the script is running inside its own dir.
        build_info = reprepbuild_info(*script_args)
        result = script_main(**build_info)
    finally:
        os.chdir(orig_workdir)

    # Analyze the imported modules for the depfile.
    # Note that a depfile is sufficient and no dyndep is needed
    # because imported Python modules are not the output of previous build tasks.
    imported_paths = set()
    for module in sys.modules.values():
        module_path = getattr(module, "__file__", None)
        if module_path is None:
            continue
        imported_paths.add(module_path)

    # Write the depfile.
    def fixpath(fn_local):
        return os.path.normpath(os.path.join(workdir, fn_local))

    outputs = [fixpath(opath) for opath in build_info.get("outputs", [])]
    strargs = check_script_args(script_args)
    outputs.append(fixpath(f"{prefix}{strargs}.log"))
    path_dep = path_py + ".d"
    write_dep(path_dep, outputs, imported_paths)

    return result


if __name__ == "__main__":
    main()
