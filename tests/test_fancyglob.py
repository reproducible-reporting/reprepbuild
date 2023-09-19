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
"""Unit tests for reprepbuild.fancyglob"""

import re

import pytest
from reprepbuild.fancyglob import (
    RE_FANCY_WILD,
    NoFancyTemplate,
    convert_fancy_to_normal,
    convert_fancy_to_regex,
    fancy_filter,
)


@pytest.mark.parametrize(
    "string, matches",
    [
        ("foo*", ["*"]),
        ("foo**", ["**"]),
        ("foo${*bar}", ["${*bar}"]),
        ("*foo${*bar}", ["*", "${*bar}"]),
        ("***foo${*bar}", ["**", "*", "${*bar}"]),
        ("**spam*foo${*bar}", ["**", "*", "${*bar}"]),
        ("*spam**foo${*bar}", ["*", "**", "${*bar}"]),
        ("*${*spam}**foo${*bar}", ["*", "${*spam}", "**", "${*bar}"]),
        ("*foo?", ["*", "?"]),
        ("?foo??", ["?", "?", "?"]),
        ("?foo[ab]?", ["?", "[ab]", "?"]),
        ("foo[?]", ["[?]"]),
        ("foo[*]", ["[*]"]),
        ("foo[${*ab}]", ["[${*ab}]"]),
        ("foo[[]a]", ["[[]"]),
    ],
)
def test_fancy_wild(string, matches):
    assert re.findall(RE_FANCY_WILD, string) == matches


@pytest.mark.parametrize(
    "fancy, normal",
    [
        ("generic/${*ch}/*.md", "generic/*/*.md"),
        ("generic/*${*ch}/*.md", "generic/*/*.md"),
        ("generic/${*ch}*/*.md", "generic/*/*.md"),
        ("generic/*${*ch}*/*.md", "generic/*/*.md"),
        ("generic/*${*ch}**/*.md", "generic/**/*.md"),
        ("generic/**${*ch}*/*.md", "generic/**/*.md"),
        ("generic/**${*ch}**/*.md", "generic/**/*.md"),
        ("generic/${*ch}${*foo}/*.md", "generic/*/*.md"),
        ("generic/${*ch}-${*foo}/*.md", "generic/*-*/*.md"),
        ("generic/${*ch}/${*foo}/*.md", "generic/*/*/*.md"),
        ("${*generic}/ch${*foo}/*.md", "*/ch*/*.md"),
        ("generic/ch${*foo}/${*md}", "generic/ch*/*"),
        ("generic/${*md}${*ch}/${*md}", "generic/*/*"),
        ("generic/${*md}?/${*md}", "generic/*/*"),
        ("generic/**?/?${*md}", "generic/**/*"),
        ("generic/?**/*?", "generic/**/*"),
        ("generic/${*md}[a[b]/?[*]", "generic/*[a[b]/?[*]"),
    ],
)
def test_fancy_to_normal(fancy, normal):
    assert convert_fancy_to_normal(fancy) == normal


@pytest.mark.parametrize(
    "fancy, regex",
    [
        ("generic/${*ch}/*.md", r"generic/(?P<ch>[^/]*)/[^/]*\.md"),
        ("generic/${*ch}/?.md", r"generic/(?P<ch>[^/]*)/[^/]\.md"),
        ("generic/${*ch}/[abc].md", r"generic/(?P<ch>[^/]*)/[abc]\.md"),
        ("generic/${*ch}/[!abc].md", r"generic/(?P<ch>[^/]*)/[^abc]\.md"),
        ("generic/${*ch}${*foo}/*.md", r"generic/(?P<ch>[^/]*)(?P<foo>[^/]*)/[^/]*\.md"),
        ("generic/${*ch}-${*foo}/*.md", r"generic/(?P<ch>[^/]*)\-(?P<foo>[^/]*)/[^/]*\.md"),
        ("generic/${*ch}/${*foo}/*.md", r"generic/(?P<ch>[^/]*)/(?P<foo>[^/]*)/[^/]*\.md"),
        ("generic/${*ch}**${*foo}/*.md", r"generic/(?P<ch>[^/]*).*(?P<foo>[^/]*)/[^/]*\.md"),
        ("${*generic}/ch${*foo}/*.md", r"(?P<generic>[^/]*)/ch(?P<foo>[^/]*)/[^/]*\.md"),
        ("generic/ch${*foo}/${*md}", r"generic/ch(?P<foo>[^/]*)/(?P<md>[^/]*)"),
        ("generic/${*md}${*ch}/${*md}", "generic/(?P<md>[^/]*)(?P<ch>[^/]*)/(?P=md)"),
    ],
)
def test_fancy_to_regex(fancy, regex):
    assert convert_fancy_to_regex(fancy) == regex


def test_nofancy_template_basics():
    t = NoFancyTemplate("word_${normal}_${*fancy}")
    assert t.substitute({"normal": "n", "*fancy": "f"}) == "word_n_f"
    assert t.substitute_nofancy({"normal": "n"}) == "word_n_${*fancy}"
    with pytest.raises(ValueError):
        t.substitute_nofancy({"normal": "n", "*fancy": "f"})
    with pytest.raises(KeyError):
        t.substitute({"normal": "n"})


def test_nofancy_template_case():
    t = NoFancyTemplate("word_${a}_${A}")
    assert t.substitute({"a": "b", "A": "B"}) == "word_b_B"


def test_fancy_filter():
    paths = [
        "path/some/foo1/some-main.txt",
        "path/some/foo1/some-main.text",
        "path/other/foo1/other-main.tex",
        "path/other/foo2/other-main.tex",
        "path/other/foo1/some-main.tex",
    ]
    keys, matches = fancy_filter(paths, "path/${*prefix}/foo*/${*prefix}-main.t??")
    assert keys == ("prefix",)
    assert len(matches) == 2
    assert matches[("some",)] == [paths[0]]
    assert matches[("other",)] == paths[2:4]
