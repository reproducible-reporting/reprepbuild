"""Unit tests for reprepbuild.utils"""


import pytest
from reprepbuild.utils import format_case_args, parse_case_args


@pytest.mark.parametrize(
    "args, argstr",
    [
        ([], ""),
        ([1, 2], "1_2"),
        (["foo", "bar"], "foo_bar"),
        # Bad idea, but expected behavior
        ([None, {}, ()], "None_{}_()"),
    ],
)
def test_format_case_nofmt(args, argstr):
    assert format_case_args(args) == argstr


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
    assert format_case_args(args, case_fmt) == case_fmt.format(*args)


@pytest.mark.parametrize(
    "kwargs, case_fmt",
    [
        ({"sth": "a", "value": 1.23}, "something_{sth}_{value:.2f}"),
        ({"rr": 1, "rrr": 2}, "{rrr}_blib_{rr}"),
        ({"w1": "foo", "w2": "bar", "w3": "spam"}, "{w2}{w3}--eggs--{w1}"),
    ],
)
def test_format_case_kwargs(kwargs, case_fmt):
    assert format_case_args(kwargs, case_fmt) == case_fmt.format(**kwargs)


@pytest.mark.parametrize(
    "args, kwargs, case_fmt",
    [
        ([], {"sth": "a", "value": 1.23}, "something_{sth}_{value:.2f}"),
        ([34, 22], {"rr": 1, "rrr": 2}, "{rrr}_{}blib{}_{rr}"),
        (["foo", "bar", "spam"], {}, "{}{}--eggs--{}"),
    ],
)
def test_format_case_args_kwargs(args, kwargs, case_fmt):
    assert format_case_args((args, kwargs), case_fmt) == case_fmt.format(*args, **kwargs)


@pytest.mark.parametrize(
    "args",
    [
        ({1: 2}, "{:d}"),
        (["foo_bar", "bluh"],),
        (["foo bar", "bluh"], "{}-{}"),
        ([("foo bar",), {}], "fff{}"),
        ([(1,), {"s": "foo bar"}], "{s}fff{}"),
    ],
)
def test_format_case_exceptions(args):
    with pytest.raises(ValueError):
        format_case_args(*args)


@pytest.mark.parametrize(
    "argstr, args, kwargs",
    [
        ("", (), {}),
        ("wawa", ("wawa",), {}),
        ("1", (1,), {}),
        ("foo_3.7", ("foo", 3.7), {}),
        ("333_lmax", (333, "lmax"), {}),
    ],
)
def test_parse_case_nofmt(argstr, args, kwargs):
    assert parse_case_args(argstr) == (args, kwargs)


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
    assert parse_case_args(argstr, case_fmt) == (args, kwargs)
