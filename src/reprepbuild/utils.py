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

__all__ = ("write_depfile", "write_dyndep")


def filter_local_files(paths):
    local = set()
    for path in paths:
        path = os.path.normpath(os.path.relpath(path))
        if not path.startswith(".."):
            local.add(path)
    return sorted(local)


def write_depfile(fn_depfile, outputs, inputs):
    """Write a depfile for outputs that depend on inputs.

    Inputs are ignored when they are not inside of the current directory (recursively).

    It is assumed that the depfile is always specified as "depfile = $out.depfile"
    and that there is only one output file.
    """
    with open(fn_depfile, "w") as f:
        f.write(" ".join(outputs))
        f.write(": \\\n")
        for ipath in filter_local_files(inputs):
            f.write(f"    {ipath} \\\n")


def write_dyndep(fn_dd, fn_out, imp_outputs, imp_inputs):
    """Write a dynamic dependency file for ninja, for a single output."""
    with open(fn_dd, "w") as f:
        f.write("ninja_dyndep_version = 1\n")
        f.write(f"build {fn_out}")
        imp_outputs = filter_local_files(imp_outputs)
        if len(imp_outputs) > 0:
            f.write(" | ")
            f.write(" ".join(imp_outputs))
        f.write(": dyndep")
        imp_inputs = filter_local_files(imp_inputs)
        if len(imp_inputs) > 0:
            f.write(" | ")
            f.write(" ".join(imp_inputs))
        f.write("\n")
