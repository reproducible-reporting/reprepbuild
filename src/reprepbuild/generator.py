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
"""A RepRepBuild Generator can produce multiple build steps for Ninja build."""

import os
import re
from collections.abc import Collection, Iterator
from glob import glob

import attrs

from .command import Command
from .fancyglob import (
    NoFancyTemplate,
    convert_fancy_to_normal,
    convert_fancy_to_regex,
    fancy_filter,
)
from .utils import CaseSensitiveTemplate

__all__ = ("BaseGenerator", "BarrierGenerator", "BuildGenerator")


def _split_if_string(arg):
    return arg.split() if isinstance(arg, str) else arg


@attrs.define
class BaseGenerator:
    def __call__(
        self, outputs: set[str], defaults: set[str]
    ) -> Iterator[tuple[(str | list | dict), list[str]]]:
        """Generate records for the Ninja build file associated with one task.

        Parameters
        ----------
        outputs
            A set filenames that preceding build steps will create.
            These will be treated as potential inputs,
            in addition to the ones found with glob.

        Yields
        ------
        records
            A list of records to be written to ``build.ninja``.
            A comment has type ``str``, defaults have type ``list``, build statements
            have type ``dict`` (and contain keyword arguments for ``Writer.build``).
        not_scanned
            A list of filenames that could not be read to find dependencies.
        """
        raise NotImplementedError


@attrs.define
class BarrierGenerator(BaseGenerator):
    """A generator to complete all builds up to a barrier, before doing the rest."""

    name: str = attrs.field(validator=attrs.validators.instance_of(str))

    def __call__(
        self, outputs: set[str], defaults: set[str]
    ) -> Iterator[tuple[(str | list | dict), list[str]]]:
        """See BaseGenerator.__call__"""
        build = {
            "outputs": [self.name],
            "rule": "phony",
            "inputs": sorted(defaults),
        }
        yield [build], []


@attrs.define
class BuildGenerator(BaseGenerator):
    """A generator from which multiple build records can be derived."""

    # A Command sub class
    command: Command = attrs.field(validator=attrs.validators.instance_of(Command))
    # If the output of that must be built, even when not required by future steps.
    default: bool = attrs.field(validator=attrs.validators.instance_of(bool))
    # The variables from the config
    variables: dict[str, str] = attrs.field(validator=attrs.validators.instance_of(dict))
    # Input paths
    inp: list[str] = attrs.field(validator=attrs.validators.instance_of(list))
    # Output paths
    out: list[str] = attrs.field(validator=attrs.validators.instance_of(list))
    # Arguments
    arg = attrs.field(default=None)
    # Phony dependencies, if any
    phony: str | None = attrs.field(
        validator=attrs.validators.optional(attrs.validators.instance_of(str)),
        default=None,
    )

    # Derive attributes
    re_ignore_safe: re.Pattern = attrs.field(init=False, default=None)

    @inp.validator
    def _validate_inp(self, _attribute, inp):
        if len(inp) == 0:
            raise ValueError(
                "A generator must have least one input, "
                f"got command {self.command.name} with arguments."
            )
        if not all(isinstance(inp_path, str) for inp_path in inp):
            raise TypeError("All input paths must be strings.")

    @out.validator
    def _validate_out(self, _attribute, out):
        if not all(isinstance(out_path, str) for out_path in out):
            raise TypeError("All output paths must be strings.")

    def __attrs_post_init__(self):
        self.re_ignore_safe = re.compile(
            "|".join(
                convert_fancy_to_regex(_pattern)
                for _pattern in self.variables.get("ignore_missing", "").split()
            )
        )

    def __call__(
        self, outputs: set[str], defaults: set[str]
    ) -> Iterator[tuple[(str | list | dict), list[str]]]:
        """See BaseGenerator.__call__"""
        # Get a file list of potentially relevant filenames for the first input
        filenames = set(glob(convert_fancy_to_normal(self.inp[0]), recursive=True))
        filenames.update(outputs)
        # Group matches for the first input
        keys, inp0_mapping = fancy_filter(filenames, self.inp[0])

        for values, inp in sorted(inp0_mapping.items()):
            # Complete the list of inputs and outputs
            inp, out = self._extend_inp_out(inp, keys, values, outputs)
            if inp is None:
                # Could not find any matches for the additional inputs.
                continue

            # Generate the raw build statements
            try:
                body_records, not_scanned = self.command.generate(
                    inp, out, self.arg, self.variables
                )
            except Exception as exc:
                exc.add_note(f"While processing generator {self}")
                raise

            # Prepare informative and cleaned-up records
            records = self._comment_records(inp, out)
            records.extend(self._post_process_records(body_records))

            # Done
            yield records, not_scanned

    def _extend_inp_out(
        self, inp: list[str], keys: Collection[str], values: Collection[str], outputs: set[str]
    ) -> tuple[list[str] | None, list[str] | None]:
        """Search for additional inputs (after the first)."""
        variables = {"*" + key: value for key, value in zip(keys, values, strict=True)}
        for inp_path in self.inp[1:]:
            inp_path = NoFancyTemplate(inp_path).substitute(variables)
            filenames = set(glob(inp_path, recursive=True))
            filenames.update(outputs)
            _, inp1_mapping = fancy_filter(filenames, inp_path)
            # If no files found, skip this generator.
            if len(inp1_mapping) == 0:
                return None, None
            inp.extend(inp1_mapping[()])
        out = [NoFancyTemplate(out_path).substitute(variables) for out_path in self.out]
        return inp, out

    def _comment_records(self, inp: list[str], out: list[str]) -> list[str]:
        """A few comments to be put before the build statements."""
        records = [
            f"command: {self.command.name}",
            "inp: " + " ".join(inp),
        ]
        if len(out) > 0:
            records.append("out: " + " ".join(out))
        if self.arg is not None:
            records.append(f" arg: {self.arg}")
        return records

    def _post_process_records(self, records: list[str | dict]) -> Iterator[str | dict]:
        """Apply general cleanups and filters to build records."""
        for record in records:
            if isinstance(record, str):
                yield record
            elif isinstance(record, dict):
                if self._skip_build(record):
                    continue
                _expand_variables(record, self.variables)
                _add_variables(record, self.command.rules[record["rule"]], self.variables)
                _add_mkdir(record)
                _clean_build(record)
                if self.phony is not None:
                    record.setdefault("order_only", []).append(self.phony)
                yield record
                if self.default:
                    yield record["outputs"]
            else:
                # defaults should not be present in command_records.
                raise NotImplementedError

    def _skip_build(self, build):
        """Skip builds that have missing inputs that are safe to ignore."""
        for input_ in build.get("inputs", []) + build.get("implicit", []):
            ignore_safe = self.re_ignore_safe.fullmatch(input_) is not None
            missing = not os.path.isfile(input_)
            if ignore_safe and missing:
                return True
        return False


def _expand_variables(build: dict, variables: dict[str, str]):
    """Expand variables and normalize paths in build record."""

    def _expand(path):
        path = CaseSensitiveTemplate(path).substitute(variables)
        if path.startswith(os.sep):
            path = os.path.relpath(path, variables["root"])
        return os.path.normpath(path)

    if "variables" in build:
        build["variables"] = {key: _expand(path) for key, path in build["variables"].items()}
    for key in "outputs", "inputs", "implicit", "order_only", "implicit_outputs":
        values = build.get(key)
        if values is not None:
            build[key] = [_expand(path) for path in values]
    depfile = build.get("depfile")
    if depfile is not None:
        build["depfile"] = _expand(depfile)


def _add_variables(build: dict, rule: dict, variables: dict[str, str]):
    """Detect variables in a build record and add known variables to the record.

    Parameters
    ----------
    build
        A build record, which is a kwargs dict for Writer.build.
        This argument is modified in place: build["variables"] is updated.
    rule
        The rule kwargs (for Writer.rule) associated with this build record.
    variables
        A dictionary with variables, which may be relevant for the build record.
    """
    # Get a list of strings to be checked for the presence of variables.
    strings = [rule.get(key) for key in ["command", "description", "depfile"]]
    strings += [
        build.get(key)
        for key in ["outputs", "inputs", "implicit", "order_only", "implicit_outputs", "dyndep"]
    ]
    strings = [item for item in strings if item is not None]
    strings = [[item] if isinstance(item, str) else item for item in strings]
    strings = sum(strings, [])

    # Detect variables present and add them to the build.
    build.setdefault("variables", {})
    for template in strings:
        for name in CaseSensitiveTemplate(template).get_identifiers():
            if name in variables:
                build["variables"][name] = variables[name]
    if len(build["variables"]) == 0:
        del build["variables"]


def _add_mkdir(build: dict):
    """Modify Ninja build record to include creation of output directories."""
    dirs_src = set()
    for key in "inputs", "implicit":
        for path_src in build.get(key, []):
            dirs_src.add(os.path.normpath(os.path.dirname(path_src)))
    dirs_src.add(".")
    dirs_dst = set()
    for key in "outputs", "implicit_outputs":
        for path_dst in build.get(key, []):
            dirs_dst.add(os.path.normpath(os.path.dirname(path_dst)))
    dirs_todo = dirs_dst - dirs_src
    if len(dirs_todo) > 0:
        build["rule"] += "_mkdir"
        build.setdefault("variables", {})["dstdirs"] = " ".join(sorted(dirs_todo))


def _clean_build(build: dict):
    """Drop empty args and prune duplicates from implicit, implicit_outputs and order_only.

    Parameters
    ----------
    build
        Dictionary with keyword arguments for Writer.build.
        This argument is modified in-place.
    """
    # Remove duplicates
    for key in "implicit", "order_only", "implicit_outputs":
        values = build.get(key)
        if values is not None:
            build[key] = sorted(set(values))
    # Remove empty lists and dicts
    for key in "inputs", "outputs", "implicit", "order_only", "implicit_outputs", "variables":
        values = build.get(key)
        if values is not None and len(values) == 0:
            del build[key]
