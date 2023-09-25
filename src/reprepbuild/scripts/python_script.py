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
"""

import argparse
import contextlib
import os
import sys

from ..utils import hide_path, import_python_path, parse_case_args, write_dep


def main() -> int:
    """Main program."""
    args = parse_args()
    return run_script(args.path_py, args.argstr)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser("rr-python-script", description="Execute a Python script")
    parser.add_argument("path_py", help="The python script whose main function will be executed.")
    parser.add_argument(
        "argstr", nargs="?", default="", help="Command-line argument for the script, if any"
    )
    return parser.parse_args()


def run_script(path_py, argstr) -> int:
    """Run the python script and collect module dependencies.

    Parameters
    ----------
    path_py
        The full path of the script.
        (It will be executed after changing directory.)
    argstr
        The arguments to the ``main`` function, encoded with
        ``reprepbuild.utils.format_case_args``.

    Returns
    -------
    exitcode
        The script exitcode.
    """
    if not path_py.endswith(".py"):
        print(f"Python script must have a .py extension. Got {path_py}")
        return 2
    workdir, fn_py = os.path.split(path_py)
    script_prefix = fn_py[:-3]

    with contextlib.chdir(workdir):
        # Load the script in its own directory
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
        case_fmt = getattr(pythonscript, "REPREPBUILD_CASE_FMT", None)

        # Execute the functions as if the script is running inside its own dir.
        script_args, script_kwargs = parse_case_args(argstr, script_prefix, case_fmt)
        build_info = reprepbuild_info(*script_args, **script_kwargs)
        os.environ["SOURCE_DATE_EPOCH"] = "315532800"
        result = script_main(**build_info)

    # Analyze the imported modules for the depfile.
    # Note that a depfile is sufficient and no dyndep is needed
    # because imported Python modules are not the output of previous build steps.
    imported_paths = set()
    for module in sys.modules.values():
        module_path = getattr(module, "__file__", None)
        if module_path is None:
            continue
        imported_paths.add(module_path)

    # Write the depfile.
    def fixpath(fn_local):
        return os.path.normpath(os.path.join(workdir, fn_local))

    # Note: only explicit outputs must be added to the depfile, not the implicit ones.
    out_prefix = fixpath(script_prefix if argstr == "" else argstr)
    outputs = [hide_path(out_prefix + ".log")]
    path_dep = hide_path(out_prefix + ".d")
    write_dep(path_dep, outputs, imported_paths)

    return result


if __name__ == "__main__":
    sys.exit(main())
