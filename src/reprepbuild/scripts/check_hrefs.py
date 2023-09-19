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
"""Check hyper references in MarkDown and PDF files."""

import argparse
import os
from enum import StrEnum, auto

import attrs
import fitz
import markdown
import requests
from bs4 import BeautifulSoup


def main():
    """Main program."""
    args = parse_args()
    hrefs = collect_hrefs(args.fn_src)
    return check_hrefs(hrefs, args.fn_src, args.fn_log)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        "rr-check-hrefs", description="Check hyper references MarkDown or PDF file."
    )
    parser.add_argument("fn_src", help="Markdown or PDF file.")
    parser.add_argument("fn_log", help="Log file with overview of check references.")
    return parser.parse_args()


@attrs.define(frozen=True)
class HRef:
    """A hyper reference to be checked."""

    url: str = attrs.field()
    allow_local: bool = attrs.field(default=True, kw_only=True)


def collect_hrefs(fn_src: str) -> list[HRef]:
    """Find all hyper references in one file."""
    if fn_src.endswith(".md"):
        return collect_hrefs_md(fn_src)
    elif fn_src.endswith(".pdf"):
        return collect_hrefs_pdf(fn_src)
    else:
        raise ValueError(f"Source file type not supported: {fn_src}")


def collect_hrefs_md(fn_md: str) -> list[HRef]:
    """Find all hyper references in one MarkDown file."""
    with open(fn_md) as f:
        html = markdown.markdown(f.read())
    soup = BeautifulSoup(html, "html.parser")
    return [HRef(link.attrs["href"]) for link in soup.find_all("a")]


def collect_hrefs_pdf(fn_pdf: str) -> list[HRef]:
    """Find all hyper references in one PDF file."""
    # See https://pymupdf.readthedocs.io/en/latest/page.html#description-of-get-links-entries
    doc = fitz.open(fn_pdf)
    hrefs = []
    for page in doc:
        for link in page.get_links():
            if link["kind"] == fitz.LINK_URI:
                # Nobody seriously uses local hyper references from PDFs.
                # Hence, allow_local=False, because it is most likely a mistake.
                hrefs.append(HRef(link["uri"], allow_local=False))
    return hrefs


class HRefStatus(StrEnum):
    PASSED = auto()
    FAILED = auto()
    IGNORED = auto()


def check_hrefs(hrefs: list[HRef], fn_src: str, fn_log: str):
    """Check the hyper references."""
    seen = set()
    screen = []
    log = []
    for href in hrefs:
        if href.url in seen:
            continue
        status = check_href(href, fn_src)
        line = f"{status}: {href.url}"
        if status == HRefStatus.FAILED:
            screen.append(line)
        log.append(line)
        seen.add(href.url)

    with open(fn_log, "w") as f:
        for line in log:
            f.write(line + "\n")
    if len(screen) > 0:
        print("\n".join(screen))
        return 1
    return 0


def check_href(href: HRef, fn_src: str) -> str:
    if href.url.startswith("mailto:"):
        return HRefStatus.IGNORED
    elif "://" in href.url:
        try:
            status_code = str(requests.get(href.url).status_code)
            if status_code[0] in "23":
                return HRefStatus.PASSED
            else:
                return HRefStatus.FAILED
        except requests.RequestException:
            return HRefStatus.FAILED
    elif href.allow_local:
        if os.path.exists(os.path.join(os.path.dirname(fn_src), href.url)):
            return HRefStatus.PASSED
    return HRefStatus.FAILED


if __name__ == "__main__":
    main()
