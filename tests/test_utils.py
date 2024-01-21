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
"""Unit tests for reprepbuild.utils"""


import pytest
from reprepbuild.utils import format_case_args, parse_case_args


@pytest.mark.parametrize("prefix", ["boo", "aa_bb", "aa__bb_"])
@pytest.mark.parametrize(
    "args, argstr",
    [
        ([], ""),
        ([1, 2], "_1_2"),
        (["foo", "bar"], "_foo_bar"),
        # Bad idea, but expected behavior
        ([None, {}, ()], "_None_{}_()"),
    ],
)
def test_format_case_nofmt(prefix, args, argstr):
    assert format_case_args(args, prefix) == prefix + argstr


@pytest.mark.parametrize(
    "args, case_fmt",
    [
        (["a", 1.23], "something_{}_{:.2f}"),
        ([1, 2], "{}_blib_{}"),
        (["foo", "bar"], "{}{}-spam"),
        # Bad idea, but expected behavior
        ([None, {}, ()], "{}@@{}!!{}"),
    ],
)
def test_format_case_fmt(args, case_fmt):
    assert format_case_args(args, None, case_fmt) == case_fmt.format(*args)
    assert format_case_args(args, "boo", case_fmt) == case_fmt.format(*args)


@pytest.mark.parametrize(
    "kwargs, case_fmt",
    [
        ({"sth": "a", "value": 1.23}, "something_{sth}_{value:.2f}"),
        ({"rr": 1, "rrr": 2}, "{rrr}_blib_{rr}"),
        ({"w1": "foo", "w2": "bar", "w3": "spam"}, "{w2}{w3}--eggs--{w1}"),
    ],
)
def test_format_case_kwargs(kwargs, case_fmt):
    assert format_case_args(kwargs, None, case_fmt) == case_fmt.format(**kwargs)
    assert format_case_args(kwargs, "boo", case_fmt) == case_fmt.format(**kwargs)


@pytest.mark.parametrize(
    "args, kwargs, case_fmt",
    [
        ([], {"sth": "a", "value": 1.23}, "something_{sth}_{value:.2f}"),
        ([34, 22], {"rr": 1, "rrr": 2}, "{rrr}_{}blib{}_{rr}"),
        (["foo", "bar", "spam"], {}, "{}{}--eggs--{}"),
    ],
)
def test_format_case_args_kwargs(args, kwargs, case_fmt):
    assert format_case_args((args, kwargs), None, case_fmt) == case_fmt.format(*args, **kwargs)
    assert format_case_args((args, kwargs), "boo", case_fmt) == case_fmt.format(*args, **kwargs)


@pytest.mark.parametrize(
    "args",
    [
        ({1: 2}, None, "{:d}"),
        (["foo_bar", "bluh"], "woo"),
        (["foo bar", "bluh"], None, "{}-{}"),
        ([("foo bar",), {}], None, "fff{}"),
        ([(1,), {"s": "foo bar"}], None, "{s}fff{}"),
    ],
)
def test_format_case_exceptions(args):
    with pytest.raises(ValueError):
        format_case_args(*args)


@pytest.mark.parametrize("prefix", ["boo", "aa_bb", "aa__bb_"])
@pytest.mark.parametrize(
    "argstr, args, kwargs",
    [
        ("", (), {}),
        ("_wawa", ("wawa",), {}),
        ("_1", (1,), {}),
        ("_foo_3.7", ("foo", 3.7), {}),
        ("_333_lmax", (333, "lmax"), {}),
    ],
)
def test_parse_case_nofmt(prefix, argstr, args, kwargs):
    assert parse_case_args(prefix + argstr, prefix) == (args, kwargs)


@pytest.mark.parametrize(
    "argstr, case_fmt, args, kwargs",
    [
        ("wawa", "{}", ("wawa",), {}),
        ("001_sowhat", "{:03d}_so{q:4}", (1,), {"q": "what"}),
        ("foo--3.7", "{bar}-{:.1f}", (-3.7,), {"bar": "foo"}),
        ("333lmax", "{lmax:d}{w}", (), {"w": "lmax", "lmax": 333}),
    ],
)
def test_parse_case_fmt(argstr, case_fmt, args, kwargs):
    assert parse_case_args(argstr, None, case_fmt) == (args, kwargs)
    assert parse_case_args(argstr, "boo", case_fmt) == (args, kwargs)
