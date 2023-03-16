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
import importlib
import os
import sys

from .utils import write_depfile


def main():
    """Main program."""
    run_script(parse_args().path_py)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser("rr-python-script")
    parser.add_argument("path_py", help="The python script whose main function will be executed.")
    return parser.parse_args()


def run_script(path):
    """Run the python script and collected module dependencies."""
    workdir, filename = os.path.split(path)
    if not filename.endswith(".py"):
        print(f"Source must have py extension. Got {workdir}/{filename}")
        sys.exit(2)

    # Check whether we're already in the eighties. (compatibility with ZIP)
    if os.environ.get("SOURCE_DATE_EPOCH") != "315532800":
        print("SOURCE_DATE_EPOCH is not set to 315532800.")
        sys.exit(1)

    orig_workdir = os.getcwd()
    workdir, fn_py = os.path.split(path)
    info = {"outputs": []}

    try:
        os.chdir(workdir)

        # Import the script and execute the main and reprepbuild_info functions.
        spec = importlib.util.spec_from_file_location("<pythonscript>", fn_py)
        pythonscript = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pythonscript)
        script_main = getattr(pythonscript, "main", None)
        if script_main is None:
            print(f"The script {path} has no main function.")
            sys.exit(1)
        reprepbuild_info = getattr(pythonscript, "reprepbuild_info", None)
        if reprepbuild_info is None:
            print(f"The script {path} has no reprepbuild_info function.")
            sys.exit(1)

        # Execute the functions as if the script is running inside its own dir.
        info = reprepbuild_info()
        script_main()
    finally:
        os.chdir(orig_workdir)

        # Analyze the imported modules for the depfile.
        # Note that a depfile is sufficient as we do not expect this
        # list to be affected by other steps in the build process.
        imported_paths = set()
        for module in sys.modules.values():
            module_path = getattr(module, "__file__", None)
            if module_path is None:
                continue
            imported_paths.add(module_path)

        # Get the outputs, needed for the depfile.
        outputs = [os.path.join(workdir, opath) for opath in info["outputs"]]

        # Write the depfile.
        write_depfile(path + ".depfile", outputs, imported_paths)


if __name__ == "__main__":
    main()
