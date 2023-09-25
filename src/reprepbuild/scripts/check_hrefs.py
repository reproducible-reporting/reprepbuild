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
"""Check hyper references in Markdown and PDF files."""

import argparse
import os
import sys
from enum import StrEnum, auto

import attrs
import fitz
import markdown
import requests
from bs4 import BeautifulSoup


def main() -> int:
    """Main program."""
    args = parse_args()
    hrefs = collect_hrefs(args.fn_src)
    if args.translate is not None:
        make_url_substitutions(hrefs, args.translate)
    check_hrefs(hrefs, args.fn_src, args.fn_log)
    return 0


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        "rr-check-hrefs", description="Check hyper references Markdown or PDF file."
    )
    parser.add_argument("fn_src", help="Markdown or PDF file.")
    parser.add_argument("fn_log", help="Log file with overview of check references.")
    parser.add_argument(
        "--translate",
        default=None,
        nargs="*",
        help="Pairs of pattern and replacement strings. "
        "This can be used to translate hyperlinks to local paths for faster checking, "
        "and is also useful when some links are behind a login.",
    )
    return parser.parse_args()


@attrs.define()
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
    """Find all hyper references in one Markdown file."""
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


def make_url_substitutions(hrefs: list[HRef], translate: list[str]):
    if len(translate) % 2 != 0:
        print("Expecting an even number of arguments to --translate.")
        return 1
    for orig, repl in zip(translate[::2], translate[1::2], strict=True):
        for href in hrefs:
            href.url = href.url.replace(orig, repl)


class HRefStatus(StrEnum):
    PASSED = auto()
    FAILED = auto()
    IGNORED = auto()


def check_hrefs(hrefs: list[HRef], fn_src: str, fn_log: str):
    """Check the hyper references."""
    seen = set()
    log = []
    broken = False
    for href in hrefs:
        if href.url in seen:
            continue
        status = check_href(href, fn_src)
        if status == HRefStatus.FAILED:
            print(f"\033[1;31;40mBROKEN LINK:\033[0;0m {href.url}")
            broken = True
        log.append(f"{status}: {href.url}\n")
        seen.add(href.url)
    if not broken:
        with open(fn_log, "w") as fh:
            fh.write("".join(log))
    return 0


def check_href(href: HRef, fn_src: str) -> str:
    if href.url.startswith("mailto:"):
        return HRefStatus.IGNORED
    elif "://" in href.url:
        session = requests.Session()
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36"
        )
        try:
            status_code = str(session.head(href.url).status_code)
            if status_code[0] == "2":
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
    sys.exit(main())
