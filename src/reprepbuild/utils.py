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
"""Utilities used in other parts of RepRepBuild."""


import os

__all__ = ("write_depfile",)


def write_depfile(fn_depfile, outputs, inputs):
    """Write a depfile for outputs that depend on inputs.

    Inputs are ignored when they are not inside of the current directory (recursively).

    It is assumed that the depfile is always specified as "depfile = $out.depfile"
    and that there is only one output file.
    """
    # Filter the inputs
    deps = set()
    for ipath in inputs:
        ipath = os.path.normpath(os.path.relpath(ipath))
        if not ipath.startswith(".."):
            deps.add(ipath)

    with open(fn_depfile, "w") as f:
        f.write(" ".join(outputs))
        f.write(": \\\n")
        for ipath in deps:
            f.write(f"    {ipath} \\\n")
