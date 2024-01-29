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
"""Glob with back-reference support.

Named wildcards have the following semantics:

- ``${*name}``: works like ``*``, but if two or more of the same named wildcards appear
  in a string, they only match when their matches are identical.
- All anonymous wildcards from glob are also supported.
"""
import re
import string
from collections.abc import Collection, Iterator
from glob import glob

RE_NAMED_WILD = re.compile(r"(\[.*?]|\$\{\*[a-zA-Z0-9_]*?}|[*]{1,2}|[?])")


__all__ = (
    "convert_named_to_normal",
    "convert_named_to_regex",
    "NoNamedTemplate",
    "glob_named",
    "filter_named",
    "filter_named_single",
)


def convert_named_to_normal(named: str) -> str:
    """Convert named wildcards to ordinary ones, compatible with builtin glob.

    Parameters
    ----------
    named
        A string with named wildcards.

    Returns
    -------
        A conventional wildcard string, without the constraint that named wildcards must correspond.
        Where possible, neighbouring wildcards are merged into one.
    """
    parts = RE_NAMED_WILD.split(named)
    for i in range(1, len(parts), 2):
        if parts[i][0] == "$":
            parts[i] = "*"
    parts = [part for part in parts if part != ""]
    texts = []
    for part in parts:
        if len(texts) == 0:
            texts.append(part)
        elif part == "?":
            if texts[-1] not in ["*", "**"]:
                texts.append("?")
        elif part == "*":
            if texts[-1] == "?":
                texts[-1] = "*"
            elif texts[-1] not in ["*", "**"]:
                texts.append("*")
        elif part == "**":
            if texts[-1] in ["*", "?"]:
                texts[-1] = "**"
            elif texts[-1] != "**":
                texts.append("**")
        else:
            texts.append(part)
    return "".join(texts)


def convert_named_to_regex(named: str) -> str:
    """Convert named wildcards to regular expressions.

    Parameters
    ----------
    named
        A string with named wildcards.

    Returns
    -------
    regex
        A regex string to test if a string matches and to extract values corresponding to
        named wildcards.
    """
    parts = RE_NAMED_WILD.split(named)
    encountered = set()
    for i, part in enumerate(parts):
        if i % 2 == 0:
            # Not a wildcard: escape regex characters.
            parts[i] = re.escape(part)
        else:
            # A named wildcard.
            # Also replace with corresponding regex.
            if part == "?":
                regex = r"[^/]"
            elif part == "*":
                regex = r"[^/]*"
            elif part == "**":
                regex = r".*"
            elif part.startswith("[") and part.endswith("]"):
                if part[1] == "!":
                    regex = rf"[^{part[2:-1]}]"
                else:
                    regex = rf"[{part[1:-1]}]"
            elif part.startswith("${*") and part.endswith("}"):
                name = part[3:-1]
                if name in encountered:
                    regex = rf"(?P={name})"
                else:
                    regex = rf"(?P<{name}>[^/]*)"
                    encountered.add(name)
            else:
                raise NotImplementedError
            parts[i] = regex
    return "".join(parts)


class NoNamedTemplate(string.Template):
    """A custom Template class to handle named wildcards.

    This class deviates from the built-in Template as follows:

    - Case sensitive
    - Accept named wildcards ${*foo}.
    - A method to substitute non-named wildcards only.
    """

    flags = re.NOFLAG
    idpattern = r"(?a:[*]?[_a-zA-Z][_a-zA-Z0-9]*)"

    def substitute_nonamed(self, mapping=None, /, **kwds):
        """Substitute ordinary fields, not ones starting with *"""
        if mapping is None:
            mapping = {}
        if any(key.startswith("*") for key in mapping):
            raise ValueError("Mapping keys starting with * not allowed in substitute_nonamed.")
        mapping = mapping | {
            key: f"${{{key}}}" for key in self.get_identifiers() if key.startswith("*")
        }
        return self.substitute(mapping, **kwds)


def glob_named(
    patterns: list[str], paths: Collection[str], do_glob: bool = True
) -> Iterator[tuple[dict[str, str], list[list[str]]]]:
    """Glob multiple patterns with named wildcards, enforcing consistency between patterns.

    Parameters
    ----------
    patterns
        A list of named glob patterns.
        Names shared by multiple patterns are forced to be consistent.
    paths
        A list of paths to consider for pattern matching, may be empty.
    do_glob
        When True, additional filenames are collected from disk.

    Yields
    ------
    match
        Each match is a tuple of a dicationary and a list of lists of ilenames.
        The dictionary relates named wildcards to values encountered in the filenames.
        The list contains one item for each pattern, i.e. a list of filenames
        matching the pattern with the named wildcard constraints.
        Multiple filenames can match because anonymous wildcards are also allowed,
        in which case they are alphabetically sorted.
    """
    # Generate candidate filenames for each pattern with glob, if needed
    if do_glob:
        candidates = []
        for pattern in patterns:
            candidates.append(glob(convert_named_to_normal(pattern), recursive=True))
    else:
        candidates = [[] for _ in patterns]

    # Use a recursive low-level routine to filter through the results from glob and given filenames.
    yield from filter_named(patterns, candidates, paths)


def filter_named(
    patterns: list[str], candidates: list[list[str]], global_candidates: Collection[str]
) -> Iterator[tuple[dict[str, str], list[list[str]]]]:
    """Filter lists of filenames used named glob patterns, enforcing consistency between patterns.

    Parameters
    ----------
    patterns
        A list of named glob patterns.
        Names shared by multiple patterns are forced to be consistent.
    candidates

    global_candidates
        A list of filenames to consider for pattern matching, may be empty.

    Yields
    ------
    Same as for ``glob_named``.
    """
    if len(patterns) == 0:
        return
    if len(patterns) != len(candidates):
        raise ValueError("The parameters patterns and candidates must have the same length.")

    local_candidates = sorted({*candidates[0], *global_candidates})
    for local_mapping, local_matches in filter_named_single(patterns[0], local_candidates):
        if len(patterns) > 1:
            other_patterns = [
                NoNamedTemplate(pattern).safe_substitute(local_mapping) for pattern in patterns[1:]
            ]
            for other_mapping, other_matches in filter_named(
                other_patterns, candidates[1:], global_candidates
            ):
                yield local_mapping | other_mapping, [local_matches, *other_matches]
        else:
            yield local_mapping, [local_matches]


def filter_named_single(
    pattern: str, paths: Collection[str]
) -> Iterator[tuple[dict[str, str], list[str]]]:
    """Filter paths that match the pattern with named wildcards.

    Parameters
    ----------
    pattern
        A (named) glob expression. See notes for details.
    paths
        A list of paths generated with glob.

    Yields
    ------
    mapping
        Relation between named wild cards and their values in the matches.
    matches
        A list of sorted paths, matching the pattern with values in the mapping.

    Notes
    -----
    If two wildcards must match the same text,
    this can be accomplished with named wildcards,
    which have the form ``${*name}``.
    For example, the following has two ``*prefix`` wildcards that must be consistent:

    .. code-block::

        path/${*prefix}/foo*/${*prefix}-main.txt

    This pattern will match the following:

    .. code-block::

        path/some/foo1/some-main.txt
        path/other/foo1/other-main.txt
        path/other/foo2/other-main.txt

    It will not match:

    .. code-block::

        path/other/foo1/some-main.txt

    The named wildcards also have a second purpose:
    The results are clustered by the values at the named wildcards.
    For the above example, the result would be:

    .. code-block:: python

        >>> from pprint import pprint
        >>> paths = [
            "path/some/foo1/some-main.txt",
            "path/other/foo1/other-main.txt",
            "path/other/foo2/other-main.txt",
            "path/other/foo1/some-main.txt",
        ]
        >>> pattern = "path/${*prefix}/foo*/${*prefix}-main.txt"
        >>> pprint(filter_named_single(pattern, paths))
        [({'*prefix': 'some'}, ['path/some/foo1/some-main.txt']),
         ({'*prefix': 'other'},
          ['path/other/foo1/other-main.txt', 'path/other/foo2/other-main.txt'])]


    The lists of filenames (values of the dictionary) are sorted alphabetically.
    """
    regex = re.compile(convert_named_to_regex(pattern))
    keys = None
    matches = {}
    for path in paths:
        match_ = regex.fullmatch(path)
        if match_ is not None:
            if keys is None:
                keys = []
                values = []
                for key, value in match_.groupdict().items():
                    keys.append(key)
                    values.append(value)
                values = tuple(values)
            else:
                gd = match_.groupdict()
                values = tuple(gd[key] for key in keys)
            matches.setdefault(values, []).append(path)
    if keys is not None:
        keys = [f"*{key}" for key in keys]
        for values, filenames in sorted(matches.items()):
            yield dict(zip(keys, values, strict=False)), sorted(filenames)
