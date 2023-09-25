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
"""Transformation of individual files."""

import os

import attrs

from ..command import Command

__all__ = ("copy", "render", "convert_svg_pdf", "convert_odf_pdf", "pdf_raster")


@attrs.define
class Transform(Command):
    _name: str = attrs.field(validator=attrs.validators.instance_of(str))
    command: str = attrs.field(validator=attrs.validators.instance_of(str))
    implicit: list[str] = attrs.field(
        kw_only=True,
        validator=attrs.validators.instance_of(list),
        default=attrs.Factory(list),
    )
    variables: dict[str, str] = attrs.field(
        validator=attrs.validators.instance_of(dict), default=attrs.Factory(dict)
    )
    new_ext: (str | None) = attrs.field(
        kw_only=True,
        validator=attrs.validators.optional(attrs.validators.instance_of(str)),
        default=None,
    )
    pool_depth: (int | None) = attrs.field(
        kw_only=True,
        validator=attrs.validators.optional(attrs.validators.instance_of(int)),
        default=None,
    )

    @implicit.validator
    def validate_implicit(self, _attribute, implicit):
        for i, imp in enumerate(implicit):
            if not isinstance(imp, str):
                raise TypeError(f"Item {i} of implicit inputs is not a string: {imp}")

    @property
    def name(self) -> str:
        """The name of the command in ``reprepbuild.yaml``."""
        return self._name

    @property
    def pools(self) -> dict[str, int]:
        return {} if self.pool_depth is None else {self._name: {"depth": self.pool_depth}}

    @property
    def rules(self) -> dict[str, dict]:
        """A dict of kwargs for Ninja's ``Writer.rule()``."""
        return {self._name: {"command": self.command}}

    def generate(
        self, inp: list[str], out: list[str], arg, variables: dict[str, str]
    ) -> tuple[list, list[str]]:
        """See Command.generate."""
        # Check parameters
        if len(out) > 1:
            raise ValueError(f"Expecting at most one destination, got {len(out)}: {out}")
        if len(inp) > 1 and len(out) == 1 and not out[0].endswith(os.sep):
            raise ValueError(f"Need directory output for multiple inputs, got {len(out)}: {out}")
        if len(out) == 0 and self.new_ext is None:
            raise ValueError("Output required because extension does not change.")
        if arg is not None:
            raise ValueError(f"Expected no arguments, got {arg}")

        # Write builds
        builds = []
        for src in inp:
            # Determine file destination
            if len(out) == 0:
                dst = os.path.splitext(src)[0] + self.new_ext
            elif out[0].endswith(os.sep):
                name = os.path.basename(src)
                if self.new_ext is not None:
                    name = os.path.splitext(name)[0] + self.new_ext
                dst = os.path.join(out[0], name)
            else:
                dst = out[0]
            build = {
                "rule": self._name,
                "outputs": [dst],
                "inputs": [src],
            }
            if len(self.implicit) > 0:
                build["implicit"] = self.implicit
            if len(self.variables) > 0:
                build["variables"] = self.variables
            if self.pool_depth is not None:
                build["pool"] = self._name
            builds.append(build)
        return builds, []


copy = Transform("copy", "cp ${in} ${out}")
render = Transform(
    "render",
    "rr-render ${in} ${out} --variables=${here}/.reprepbuild/variables.json",
    implicit=["${here}/.reprepbuild/variables.json"],
)
convert_svg_pdf = Transform(
    "convert_svg_pdf",
    "${inkscape} ${in} -T --export-filename=${out} --export-type=pdf > /dev/null"
    "&& rr-pdf-normalize ${out}",
    variables={"inkscape": "inkscape"},
    new_ext=".pdf",
    # The conversion seems to crash when running concurrently.
    pool_depth=1,
)
convert_odf_pdf = Transform(
    "convert_odf_pdf",
    # Hacky workaround for the poor CLI of libreoffice ...
    "WORK=`mktemp -d --suffix=reprepbuild` && "
    "${libreoffice} --convert-to pdf ${in} --outdir $$WORK > /dev/null && "
    "cp $$WORK/*.pdf ${out} && "
    "rm -r $$WORK &&"
    # Libreoffice inserts random PDF Trailer IDs, which we don't like...
    "rr-pdf-normalize ${out}",
    variables={"libreoffice": "libreoffice"},
    new_ext=".pdf",
    # The conversion seems to crash when running concurrently.
    pool_depth=1,
)
pdf_raster = Transform(
    "pdf_raster",
    "${gs} -sDEVICE=pdfimage24 -dNOPAUSE -dBATCH -dSAFER "
    "-r${raster_dpi} -sOutputFile=${out} ${in} > /dev/null",
    variables={"gs": "gs", "raster_dpi": "150"},
)
