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
"""Built-in RepRepBuild commands."""


from .check_hrefs import check_hrefs
from .latex import latex, latex_diff, latex_flat
from .mupdf import pdf_add_notes, pdf_merge, pdf_nup
from .python_script import python_script
from .render import render
from .shell_script import shell_script
from .transform import (
    convert_odf_pdf,
    convert_pdf_png,
    convert_svg_pdf,
    copy,
    markdown_pdf,
    pdf_raster,
)
from .zip import zip_latex, zip_manifest, zip_plain

__all__ = ("get_commands",)


def get_commands():
    return [
        check_hrefs,
        latex,
        latex_flat,
        latex_diff,
        pdf_add_notes,
        pdf_merge,
        pdf_nup,
        python_script,
        convert_odf_pdf,
        convert_svg_pdf,
        convert_pdf_png,
        copy,
        markdown_pdf,
        pdf_raster,
        render,
        shell_script,
        zip_latex,
        zip_manifest,
        zip_plain,
    ]
