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
"""Glob with backreference support."""

import re
import string
from collections.abc import Collection

RE_FANCY_WILD = re.compile(r"(\[.*?]|\$\{\*[a-zA-Z0-9_]*?}|[*]{1,2}|[?])")


__all__ = ("convert_fancy_to_normal", "convert_fancy_to_regex", "NoFancyTemplate", "fancy_filter")


def convert_fancy_to_normal(fancy: str) -> str:
    """Convert fancy wildcards to ordinary ones, compatible with builtin glob."""
    parts = RE_FANCY_WILD.split(fancy)
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


def convert_fancy_to_regex(fancy: str) -> str:
    """Convert fancy wildcards to regular expressions."""
    parts = RE_FANCY_WILD.split(fancy)
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


class NoFancyTemplate(string.Template):
    """A custom Template class to handle fancy wildcards.

    This class deviates from the built-in Template as follows:

    - Case sensitive
    - Accept fancyglob wildcards ${*foo}.
    - Add a method to substitute non-fancyglob wildcards only
    """

    flags = re.NOFLAG
    idpattern = r"(?a:[*]?[_a-zA-Z][_a-zA-Z0-9]*)"

    def substitute_nofancy(self, mapping=None, /, **kwds):
        """Substitute ordinary fields, not ones starting with *"""
        if mapping is None:
            mapping = {}
        if any(key.startswith("*") for key in mapping):
            raise ValueError("Mapping keys starting with * not allowed in substitute_nofancy.")
        mapping = mapping | {
            key: f"${{{key}}}" for key in self.get_identifiers() if key.startswith("*")
        }
        return self.substitute(mapping, **kwds)


def fancy_filter(
    paths: Collection[str], fancy: str
) -> tuple[tuple[str, ...], dict[tuple[str, ...], list[str]]]:
    """Filter results from ordinary glob with the fancy glob string.

    Parameters
    ----------
    paths
        A list of paths generated with glob.
    fancy
        A fancy glob expression. See notes for details.

    Returns
    -------
    keys
        A tuple with names of named wildcards.
    matches
        A key is a tuple of strings matched by the named wildcards.
        The value is a list of paths matching with those values at the named wildcards.

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
    The results are clustered by the values at the named wildcards,
    and returned as a tuple of a wildcard keys and a dictionary of matches.
    For the above example, the result would be:

    .. code-block:: python

        >>> from pprint import pprint
        >>> paths = [
            "path/some/foo1/some-main.txt",
            "path/other/foo1/other-main.txt",
            "path/other/foo2/other-main.txt",
            "path/other/foo1/some-main.txt",
        ]
        >>> fancy = "path/${*prefix}/foo*/${*prefix}-main.txt"
        >>> pprint(fancy_filter(paths, fancy))
        (('prefix',),
         {('other',): ['path/other/foo1/other-main.txt',
                       'path/other/foo2/other-main.txt'],
          ('some',): ['path/some/foo1/some-main.txt']})

    The lists of filenames (values of the dictionary) are sorted alphabetically.
    """
    regex = re.compile(convert_fancy_to_regex(fancy))
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
                keys = tuple(keys)
                values = tuple(values)
            else:
                gd = match_.groupdict()
                values = tuple(gd[key] for key in keys)
            matches.setdefault(values, []).append(path)
    if keys is None:
        return (), {}
    for filenames in matches.values():
        filenames.sort()
    return keys, matches
