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
"""Markdown to (HTML and) PDF conversion."""


import argparse
import re
import sys
import tempfile

import markdown
import weasyprint

__all__ = ("convert_markdown",)


HTML_HEADER = """\
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="" xml:lang="">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes" />
  <title>Preview</title>
  <style>
    html {
      line-height: 1.3;
      font-family: IBM Plex Sans, Georgia, serif;
      font-size: 10pt;
    }
    h1, h2 {
      margin-top: 1cm;
      border-bottom: 1pt solid #DDDDDD;
    }
    h3, h4, p {
      margin-top: 0.5cm;
      padding-left: 1.0cm;
    }
    ul {
      padding-left: 2.0cm;
    }
    ul ul {
      padding-left: 1.0cm;
    }
    li {
      margin-top: 2pt;
      margin-bottom: 2pt;
    }
    code {
      font-family: IBM Plex Mono;
      background-color: rgba(175, 184, 193, 0.2);
      padding: 2pt 5pt 2pt 5pt;
      border-radius: 6pt;
    }
    table {
      margin-left: auto;
      margin-right: auto;
      text-align: center;
      border-collapse: collapse;
    }
    td, th {
      border: 1pt solid #BBBBBB;
      padding: 4pt;
      font-size: 10pt;
    }
    @page {
        size: A4;
        margin: 1.5cm 1.5cm 1.5cm 1.5cm;
    }
  </style>
</head>
<body>
"""

HTML_FOOTER = "</body>"


MACRO_TEXT = r"""\
\bvec:\vec{\mathbf{#1}}
\normvec:\hat{\mathbf{#1}}
\d:\operatorname{d}\!{#1}
\ihat:\hat{\mathbf{i}}
\jhat:\hat{\mathbf{j}}
\khat:\hat{\mathbf{k}}
"""


def convert_markdown(text_md, *, fn_html=None, fn_pdf=None):
    """Convert Markdown to HTML and PDF with KaTeX support.

    Parameters
    ----------
    text_md
        The markdown source text
    fn_html
        A HTML output filename.
    fn_pdf
        A PDF output filename.
    """
    # Check output arguments
    if fn_html is None and fn_pdf is None:
        raise ValueError("No HTML or PDF output provided.")

    # Convert conventional LaTeX equation syntax to make it compatible with markdown_katex
    text_md = re.sub(r"\B\$(\S|\S[^\n\r]*?\S)\$\B", r"$`\1`$", text_md)

    # Write macros to temporary file for KaTeX.
    with tempfile.NamedTemporaryFile(suffix=".tex") as f:
        f.write(MACRO_TEXT.encode("ascii"))
        f.flush()
        fn_macro = f.name

        md_ctx = markdown.Markdown(
            extensions=[
                "fenced_code",
                "markdown_katex",
                "tables",
            ],
            extension_configs={
                "markdown_katex": {"insert_fonts_css": True, "macro-file": fn_macro}
            },
        )

        # Convert to HTML
        text_html = HTML_HEADER + md_ctx.convert(text_md) + HTML_FOOTER

    # Optionally write HTML
    if fn_html is not None:
        with open(fn_html, "w") as f:
            f.write(text_html)

    # Optionally convert to PDF
    if fn_pdf is not None:
        html = weasyprint.HTML(string=text_html)
        html.write_pdf(fn_pdf)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="rr-markdown-pdf", description="Convert Markdown to HTML and/or PDF"
    )
    parser.add_argument("markdown", help="A Markdown file with extension `.md`")
    parser.add_argument("--pdf", help="A PDF output filename")
    parser.add_argument("--html", help="A HTML output filename")
    return parser.parse_args()


def main() -> int:
    """Main program."""
    args = parse_args()
    fn_md = args.markdown
    if not fn_md.endswith(".md"):
        raise ValueError("The markdown file must end with the .md extension.")
    with open(fn_md) as f:
        convert_markdown(f.read(), fn_html=args.html, fn_pdf=args.pdf)
    return 0


if __name__ == "__main__":
    sys.exit(main())
