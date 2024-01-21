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
"""Helper functions for python scripts in document repositories."""


import attrs
import numpy as np
from scipy import optimize

try:
    import fitz_new as fitz
except ImportError:
    import fitz


__all__ = ("SubFigure", "layout_sub_figures")


@attrs.define
class SubFigure:
    irow: int = attrs.field()
    icol: int = attrs.field()
    label: str = attrs.field()
    fn_pdf: str = attrs.field()
    nrow: int = attrs.field(default=1)
    ncol: int = attrs.field(default=1)
    pdf = attrs.field(default=None)


def layout_sub_figures(
    fn_pdf,
    sub_figures,
    fontname="hebo",
    fontfile=None,
    fontsize=7,
    lineheight=10,
    padding=5,
    hshift=0,
):
    """Combine PDF sub-figures into a single PDF with labels on top of each sub-figure.

    Parameters
    ----------
    fn_pdf
        The PDF output file.
    sub_figures
        The list sub figures, instances of the SubFigure class.
    fontname
        A Fontname recognized by PyMyPDF or a custom name when fontfile is specified.
    fontfile
        None or the path to a ttf file.
        When used, specify a corresponding fontname (of your choice).
    fontsize
        The fontsize to use for the labels
    lineheight
        The line height to use for the labels
    padding
        The padding added added to the subfigures before combining them.
        This parameter is also used as margin between the label and the figure.
    hshift
        An optional horizontal displacement of the subfigure label.
    """
    _load_pdfs(sub_figures)
    for sub_figure in sub_figures:
        _add_label(sub_figure, fontname, fontfile, fontsize, lineheight, padding, hshift)
    out = _combine_figures(sub_figures)
    out.set_metadata({})
    out.del_xml_metadata()
    out.scrub()
    out.save(fn_pdf, garbage=4, deflate=True, linear=True, no_new_id=True)


def _load_pdfs(sub_figures):
    for sf in sub_figures:
        sf.pdf = fitz.open(sf.fn_pdf)
        if sf.pdf.page_count != 1:
            raise ValueError(
                "Subfigure PDF files should have just one page. "
                f"Found {sf.pdf.page_count} in {sf.fn_pdf}"
            )


def _add_label(sub_figure, fontname, fontfile, fontsize, lineheight, padding, hshift):
    new = fitz.open()
    old_page = sub_figure.pdf[0]
    new_page = new.new_page(
        width=old_page.rect.width + 2 * padding,
        height=old_page.rect.height + lineheight + 3 * padding,
    )
    top = lineheight + 2 * padding
    new_page.show_pdf_page(
        fitz.Rect(
            padding,
            top,
            old_page.rect.width + padding,
            old_page.rect.height + top,
        ),
        sub_figure.pdf,
        0,
    )
    font = fitz.Font(fontname, fontfile)
    length = font.text_length(sub_figure.label, fontsize=fontsize)
    text_writer = fitz.TextWriter(new_page.rect)
    text_writer.append(
        fitz.Point((new_page.rect.width - length) / 2 + hshift, padding + lineheight),
        sub_figure.label,
        font=font,
        fontsize=fontsize,
    )
    text_writer.write_text(new_page)
    sub_figure.pdf = new


def _combine_figures(sub_figures):
    # Basic settings
    nrow = 1
    ncol = 1
    for sf in sub_figures:
        nrow = max(nrow, sf.irow + sf.nrow)
        ncol = max(ncol, sf.icol + sf.ncol)

    # Define optimization variables
    row_vars = np.arange(nrow)
    col_vars = np.arange(ncol) + nrow
    nvar = nrow + ncol

    # Run over subfigures and define constraints
    a_ub = np.zeros((2 * len(sub_figures), nvar))
    b_ub = np.zeros(2 * len(sub_figures))
    c = np.zeros(nvar)
    c[row_vars[-1]] = 1
    c[col_vars[-1]] = 1
    ieq = 0
    for sf in sub_figures:
        if sf.irow == 0:
            a_ub[ieq, row_vars[sf.nrow - 1]] = -1
        else:
            a_ub[ieq, row_vars[sf.irow + sf.nrow - 1]] = -1
            a_ub[ieq, row_vars[sf.irow - 1]] = 1
        b_ub[ieq] = -(sf.pdf[0].rect.height)
        ieq += 1
        if sf.icol == 0:
            a_ub[ieq, col_vars[sf.ncol - 1]] = -1
        else:
            a_ub[ieq, col_vars[sf.icol + sf.ncol - 1]] = -1
            a_ub[ieq, col_vars[sf.icol - 1]] = 1
        b_ub[ieq] = -(sf.pdf[0].rect.width)
        ieq += 1

    # Optimize the layout
    res = optimize.linprog(c, a_ub, b_ub)
    rowres = np.concatenate([[0.0], res.x[:nrow]])
    colres = np.concatenate([[0.0], res.x[nrow:]])

    # Put everything in one PDF
    out = fitz.open()
    page = out.new_page(width=colres[-1], height=rowres[-1])
    for sf in sub_figures:
        dst_rect = fitz.Rect(
            colres[sf.icol],
            rowres[sf.irow],
            colres[sf.icol + sf.ncol],
            rowres[sf.irow + sf.nrow],
        )
        page.show_pdf_page(dst_rect, sf.pdf, 0)
    return out
