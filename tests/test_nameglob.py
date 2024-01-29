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
"""Unit tests for reprepbuild.namedglob"""
import contextlib
import os
import re

import pytest
from reprepbuild.nameglob import (
    RE_NAMED_WILD,
    NoNamedTemplate,
    convert_named_to_normal,
    convert_named_to_regex,
    filter_named,
    filter_named_single,
    glob_named,
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
def test_named_wild(string, matches):
    assert re.findall(RE_NAMED_WILD, string) == matches


@pytest.mark.parametrize(
    "named, normal",
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
def test_named_to_normal(named, normal):
    assert convert_named_to_normal(named) == normal


@pytest.mark.parametrize(
    "named, regex",
    [
        ("generic/${*ch}/*.md", r"generic/(?P<ch>[^/]*)/[^/]*\.md"),
        ("generic/${*ch}/?.md", r"generic/(?P<ch>[^/]*)/[^/]\.md"),
        ("generic/${*ch}/[abc].md", r"generic/(?P<ch>[^/]*)/[abc]\.md"),
        ("generic/${*ch}/[!abc].md", r"generic/(?P<ch>[^/]*)/[^abc]\.md"),
        ("generic/${*ch}${*foo}/*.md", r"generic/(?P<ch>[^/]*)(?P<foo>[^/]*)/[^/]*\.md"),
        ("generic/${*ch}-${*foo}/*.md", r"generic/(?P<ch>[^/]*)\-(?P<foo>[^/]*)/[^/]*\.md"),
        ("generic/${*ch}/${*foo}/*.md", r"generic/(?P<ch>[^/]*)/(?P<foo>[^/]*)/[^/]*\.md"),
        ("generic/${*ch}**${*foo}/*.md", r"generic/(?P<ch>[^/]*).*(?P<foo>[^/]*)/[^/]*\.md"),
        ("generic/${*ch}**/${*foo}/*.md", r"generic/(?P<ch>[^/]*).*/(?P<foo>[^/]*)/[^/]*\.md"),
        ("${*generic}/ch${*foo}/*.md", r"(?P<generic>[^/]*)/ch(?P<foo>[^/]*)/[^/]*\.md"),
        ("generic/ch${*foo}/${*md}", r"generic/ch(?P<foo>[^/]*)/(?P<md>[^/]*)"),
        ("generic/${*md}${*ch}/${*md}", "generic/(?P<md>[^/]*)(?P<ch>[^/]*)/(?P=md)"),
    ],
)
def test_named_to_regex(named, regex):
    assert convert_named_to_regex(named) == regex


def test_named_to_regex_groups():
    regex = re.compile(convert_named_to_regex("generic/${*ch}**/${*foo}/*.md"))
    match_ = regex.fullmatch("generic/ch1/some/some/name/file.md")
    assert match_.groups() == ("ch1", "name")


def test_nonamed_template_basics():
    t = NoNamedTemplate("word_${normal}_${*named}")
    assert t.substitute({"normal": "n", "*named": "f"}) == "word_n_f"
    assert t.substitute_nonamed({"normal": "n"}) == "word_n_${*named}"
    assert t.safe_substitute({"*named": "f"}) == "word_${normal}_f"
    with pytest.raises(ValueError):
        t.substitute_nonamed({"normal": "n", "*named": "f"})
    with pytest.raises(KeyError):
        t.substitute({"normal": "n"})


def test_nonamed_template_case():
    t = NoNamedTemplate("word_${a}_${A}")
    assert t.substitute({"a": "b", "A": "B"}) == "word_b_B"


def test_filter_named_single_simple():
    paths = [
        "path/some/foo1/some-main.txt",
        "path/other/foo1/other-main.txt",
        "path/other/foo2/other-main.txt",
        "path/other/foo1/some-main.txt",
    ]
    pattern = "path/${*prefix}/foo*/${*prefix}-main.txt"

    it = filter_named_single(pattern, paths)
    assert next(it) == (
        {"*prefix": "other"},
        ["path/other/foo1/other-main.txt", "path/other/foo2/other-main.txt"],
    )
    assert next(it) == ({"*prefix": "some"}, ["path/some/foo1/some-main.txt"])
    with pytest.raises(StopIteration):
        next(it)


def test_filter_named_single_anonymous():
    paths = [
        "path/some/foo1/some-main.txt",
        "path/other/foo1/other-main.txt",
        "path/other/foo2/other-main.txt",
        "path/other/foo1/some-main.txt",
    ]
    pattern = "path/*/foo*/*-main.txt"

    it = filter_named_single(pattern, paths)
    assert next(it) == ({}, sorted(paths))
    with pytest.raises(StopIteration):
        next(it)


def _make_loc_files(loc: list[str]):
    for paths in loc:
        for path in paths:
            dn = os.path.dirname(path)
            if not os.path.isdir(dn):
                os.makedirs(dn)
            with open(path, "w"):
                pass


@pytest.mark.parametrize(
    "loc, glo",
    [
        (
            [[], []],
            [
                "b/foo.txt",
                "a/foo.txt",
                "b/bar3.csv",
                "b/bir4.csv",
                "b/bar5.csv",
                "a/bar1.csv",
                "a/bir1.csv",
                "a/bar2.csv",
            ],
        ),
        (
            [["b/foo.txt", "a/foo.txt"], []],
            ["b/bar3.csv", "b/bir4.csv", "b/bar5.csv", "a/bar1.csv", "a/bir1.csv", "a/bar2.csv"],
        ),
        (
            [
                [],
                [
                    "b/bar3.csv",
                    "b/bir4.csv",
                    "b/bar5.csv",
                    "a/bar1.csv",
                    "a/bir1.csv",
                    "a/bar2.csv",
                ],
            ],
            ["b/foo.txt", "a/foo.txt"],
        ),
        (
            [
                ["b/foo.txt", "a/foo.txt"],
                [
                    "b/bar3.csv",
                    "b/bir4.csv",
                    "b/bar5.csv",
                    "a/bar1.csv",
                    "a/bir1.csv",
                    "a/bar2.csv",
                ],
            ],
            [],
        ),
    ],
)
def test_filter_named1(loc, glo, tmpdir):
    patterns = ["${*dir}/foo.txt", "${*dir}/b?r${*id}.csv"]
    expected = [
        ({"*dir": "a", "*id": "1"}, [["a/foo.txt"], ["a/bar1.csv", "a/bir1.csv"]]),
        ({"*dir": "a", "*id": "2"}, [["a/foo.txt"], ["a/bar2.csv"]]),
        ({"*dir": "b", "*id": "3"}, [["b/foo.txt"], ["b/bar3.csv"]]),
        ({"*dir": "b", "*id": "4"}, [["b/foo.txt"], ["b/bir4.csv"]]),
        ({"*dir": "b", "*id": "5"}, [["b/foo.txt"], ["b/bar5.csv"]]),
    ]
    it = filter_named(patterns, loc, glo)
    assert list(it) == expected
    with contextlib.chdir(tmpdir):
        _make_loc_files(loc)
        it2 = glob_named(patterns, glo)
        assert list(it2) == expected


@pytest.mark.parametrize(
    "loc, glo",
    [
        ([[], []], ["b/foo.txt", "a/foo.txt", "other/spam.txt", "other/egg.txt"]),
        ([[], ["other/spam.txt", "other/egg.txt"]], ["b/foo.txt", "a/foo.txt"]),
        ([["b/foo.txt", "a/foo.txt"], []], ["other/spam.txt", "other/egg.txt"]),
        ([["b/foo.txt", "a/foo.txt"], ["other/spam.txt", "other/egg.txt"]], []),
        ([["b/foo.txt", "a/foo.txt"], ["other/spam.txt", "other/egg.txt"]], ["other/egg.txt"]),
    ],
)
def test_filter_named2(loc, glo, tmpdir):
    patterns = ["${*dir}/foo.txt", "other/${*name}.txt"]
    expected = [
        ({"*dir": "a", "*name": "egg"}, [["a/foo.txt"], ["other/egg.txt"]]),
        ({"*dir": "a", "*name": "spam"}, [["a/foo.txt"], ["other/spam.txt"]]),
        ({"*dir": "b", "*name": "egg"}, [["b/foo.txt"], ["other/egg.txt"]]),
        ({"*dir": "b", "*name": "spam"}, [["b/foo.txt"], ["other/spam.txt"]]),
    ]
    it1 = filter_named(patterns, loc, glo)
    assert list(it1) == expected
    with contextlib.chdir(tmpdir):
        _make_loc_files(loc)
        it2 = glob_named(patterns, glo)
        assert list(it2) == expected
