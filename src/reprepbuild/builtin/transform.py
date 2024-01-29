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
import re
from collections.abc import Callable
from mmap import mmap

import attrs

from ..command import Command

__all__ = (
    "copy",
    "convert_svg_pdf",
    "convert_odf_pdf",
    "convert_pdf_png",
    "pdf_raster",
    "markdown_pdf",
)


@attrs.define
class Transform(Command):
    # The name used in reprepbuild.yaml
    _name: str = attrs.field(validator=attrs.validators.instance_of(str))
    # The command-line in the Ninja build rule
    command: str = attrs.field(validator=attrs.validators.instance_of(str))
    # A list of implicit inputs
    generate_implicit: Callable | None = attrs.field(
        kw_only=True,
        validator=attrs.validators.optional(attrs.validators.is_callable()),
        default=None,
    )
    # Variables used in the command and there default values.
    # This dictionary contains default values,
    # which may be replaced by user-specified values.
    variables: dict[str, str] = attrs.field(
        validator=attrs.validators.instance_of(dict), default=attrs.Factory(dict)
    )
    # The new file extension of the conversion output.
    new_ext: str | None = attrs.field(
        kw_only=True,
        validator=attrs.validators.optional(attrs.validators.instance_of(str)),
        default=None,
    )
    # If at most a given number of transformations can run in parallel,
    # specify this number as the pool depth.
    # When not specified, parallelism is not constrained.
    pool_depth: int | None = attrs.field(
        kw_only=True,
        validator=attrs.validators.optional(attrs.validators.instance_of(int)),
        default=None,
    )

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

    def generate(self, inp: list[str], out: list[str], arg) -> tuple[list, list[str]]:
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
        gendeps = []
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
            if os.path.abspath(src) == os.path.abspath(dst):
                raise ValueError(f"Input file equals output file: {src}")
            build = {
                "rule": self._name,
                "outputs": [dst],
                "inputs": [src],
            }
            if self.generate_implicit is not None:
                implicit, inp_gendeps = self.generate_implicit(src, arg)
                if len(implicit) > 0:
                    build["implicit"] = implicit
                gendeps.extend(inp_gendeps)
            if len(self.variables) > 0:
                build["variables"] = self.variables.copy()
            if self.pool_depth is not None:
                build["pool"] = self._name
            builds.append(build)
        return builds, gendeps


RE_OPTIONS = re.MULTILINE | re.DOTALL
RE_SVG_HREF = re.compile(rb"<image [^<]*?href=\"(?!#)(?!data:)(.*?)\"[^<]*?>", RE_OPTIONS)


def _generate_implicit_svg(src: str, _arg) -> tuple[list[str], list[str]]:
    """Search implicit dependencies in SVG files, specifically (recursively) included images."""
    implicit = []
    gendeps = [src]
    idep = 0
    while idep < len(gendeps):
        path_svg = gendeps[idep]
        # It is generally a poor practice to parse XML with a regular expression,
        # unless performance becomes an issue...
        with open(path_svg, "r+") as fh:
            data = mmap(fh.fileno(), 0)
            hrefs = re.findall(RE_SVG_HREF, data)

        # Process hrefs
        for href in hrefs:
            href = href.decode("utf-8")
            if href.startswith("file://"):
                href = href[7:]
            if "://" not in href:
                if not href.startswith("/"):
                    href = os.path.join(os.path.dirname(path_svg), href)
                implicit.append(href)
                if href.endswith(".svg"):
                    gendeps.append(href)
        idep += 1

    return implicit, gendeps


copy = Transform("copy", "cp ${in} ${out}")
convert_svg_pdf = Transform(
    "convert_svg_pdf",
    "${inkscape} ${in} -T --export-filename=${out} --export-type=pdf > /dev/null"
    "&& rr-pdf-normalize ${out}",
    generate_implicit=_generate_implicit_svg,
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
convert_pdf_png = Transform(
    "convert_pdf_png",
    "${mutool} draw -o ${out} -r ${dpi} ${in} 2> /dev/null",
    variables={"mutool": "mutool", "dpi": "600"},
    new_ext=".png",
)
pdf_raster = Transform(
    "pdf_raster",
    "${gs} -sDEVICE=pdfimage24 -dNOPAUSE -dBATCH -dSAFER "
    "-r${raster_dpi} -sOutputFile=${out} ${in} > /dev/null",
    variables={"gs": "gs", "raster_dpi": "150"},
)
markdown_pdf = Transform("markdown_pdf", "rr-markdown-pdf ${in} --pdf ${out}", new_ext=".pdf")
