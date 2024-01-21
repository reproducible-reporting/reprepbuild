# RepRepBuild is the build tool for Reproducible Reporting.
# Copyright (C) 2024 Toon Verstraelen
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
"""Render a file with Jinja2."""


import argparse
import os
import sys

import jinja2

from ..utils import load_constants


def main() -> int:
    """Main program."""
    args = parse_args()
    root = os.getcwd()
    cwd = os.path.dirname(args.path_in)
    constants = load_constants(root, cwd, args.constants)
    if args.mode == "plain":
        latex = False
    elif args.mode == "latex":
        latex = True
    elif args.mode == "auto":
        latex = args.path_out.endswith(".tex")
    else:
        raise ValueError(f"mode not supported: {args.mode}")
    dir_out = os.path.normpath(os.path.dirname(args.path_out))
    result = render(args.path_in, constants, latex, dir_out=dir_out)
    with open(args.path_out, "w") as fh:
        fh.write(result)
    return 0


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(prog="rr-render", description="Render a file with Jinja2.")
    parser.add_argument("path_in", help="The input file")
    parser.add_argument("constants", nargs="+", help="JSON files with constants")
    parser.add_argument("path_out", help="The output file")
    parser.add_argument(
        "--mode",
        choices=["auto", "plain", "latex"],
        help="The delimiter style to use",
        default="auto",
    )
    return parser.parse_args()


def render(
    path_template: str,
    variables: dict[str, str],
    latex: bool = False,
    *,
    str_in: str | None = None,
    dir_out: str | None = None,
) -> str:
    """The template is processed with jinja and returned after filling in variables.

    Parameters
    ----------
    path_template
        The filename of the template to load, may be a mock
    variables
        A dictionary of variables to substitute into the template.
    latex
        When True, the angle-version of the template codes is used, e.g. `<%` etc.
    str_in
        The template string.
        When given path_templates is not loaded and only used for error messages.
    dir_out
        This is used by the relpath filter, which allows converting absolute to relative paths.

    Returns
    -------
    str_out
        A string with the result.
    """
    # Customize Jinja 2 environment
    env_kwargs = {
        "keep_trailing_newline": True,
        "trim_blocks": True,
        "undefined": jinja2.StrictUndefined,
    }
    if latex:
        env_kwargs.update(
            {
                "block_start_string": "<%",
                "block_end_string": "%>",
                "variable_start_string": "<<",
                "variable_end_string": ">>",
                "comment_start_string": "<#",
                "comment_end_string": "#>",
                "line_statement_prefix": "%==",
            }
        )
    env = jinja2.Environment(**env_kwargs)

    # Add custom filter
    if dir_out is not None:
        env.filters["relpath"] = lambda path: os.path.normpath(os.path.relpath(path, dir_out))

    # Load template and use it
    if str_in is None:
        with open(path_template) as f:
            str_in = f.read()
    template = env.from_string(str_in)
    template.filename = path_template
    return template.render(**variables)


if __name__ == "__main__":
    sys.exit(main())
