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
"""A RepRepBuild Generator can produce multiple build steps for Ninja build."""

import os
import re
from collections.abc import Iterator

import attrs

from .command import Command
from .nameglob import NoNamedTemplate, convert_named_to_regex, glob_named
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
        defaults
            A list of files to be built by default when ninja is not called with
            any targets on the command line.

        Yields
        ------
        records
            A list of records to be written to ``build.ninja``.
            A comment has type ``str``, defaults have type ``list``, build statements
            have type ``dict`` (and contain keyword arguments for ``Writer.build``).
        gendeps
            A list of filenames that were (or should have been) read
            to determine the build records.
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
        # The phony of the barrier represents all previous defaults,
        # so we can clear the list and use the phony instead.
        defaults.clear()
        defaults.add(self.name)
        yield [build], []


@attrs.define
class BuildGenerator(BaseGenerator):
    """A generator from which multiple build records can be derived."""

    # A Command sub class
    command: Command = attrs.field(validator=attrs.validators.instance_of(Command))
    # Input paths
    inp: list[str] = attrs.field(validator=attrs.validators.instance_of(list))
    # Output paths
    out: list[str] = attrs.field(
        validator=attrs.validators.instance_of(list), default=attrs.Factory(list)
    )
    # The variables from the environment
    constants: dict[str, str] = attrs.field(
        validator=attrs.validators.instance_of(dict), default=attrs.Factory(dict)
    )
    # Arguments
    arg = attrs.field(default=None)
    # Whether the output must be built, even when not required by future steps.
    default: bool = attrs.field(converter=bool, default=True)
    # Whether it is acceptable that not inputs can be matched with self.inp
    optional: bool = attrs.field(converter=bool, default=False)
    # When true, only previous outputs are considered as inputs.
    built_inputs_only: bool = attrs.field(converter=bool, default=False)
    # Phony dependencies, if any
    phony_deps: list[str] | None = attrs.field(
        validator=attrs.validators.optional(attrs.validators.instance_of(list)),
        default=attrs.Factory(list),
    )

    # Derived attributes
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
                convert_named_to_regex(_pattern)
                for _pattern in self.constants.get("ignore_missing", "").split()
            )
        )

    def __call__(
        self, outputs: set[str], defaults: set[str]
    ) -> Iterator[tuple[(str | list | dict), list[str]]]:
        """See BaseGenerator.__call__"""
        matched = False
        for names, inp_groups in glob_named(self.inp, outputs, not self.built_inputs_only):
            # Complete the list of inputs and outputs
            matched = True
            inp, out = self._extend_inp_out(names, inp_groups)
            records = self._comment_records(inp, out)

            filter_comment = _test_filter_inp(inp)
            if filter_comment is not None:
                records.append(filter_comment)
                yield records, []
                continue

            # Generate the raw build statements
            try:
                cmd_records, gendeps = self.command.generate(inp, out, self.arg)
            except Exception as exc:
                exc.add_note(f"- Generator: {self}")
                for comment in records:
                    exc.add_note(f"- {comment}")
                raise

            # Prepare informative and cleaned-up records
            records.extend(self._post_process_records(cmd_records))

            # Done
            yield records, gendeps

        if not matched:
            records = [
                "Could not find suitable inputs. ",
                f"- command: {self.command.name}"
                f"- inp: {self.inp}"
                f"- out: {self.out}"
                f"- arg: {self.arg}",
            ]
            if self.optional:
                yield records, []
            else:
                raise ValueError("\n".join(records))

    def _extend_inp_out(
        self, names: dict[str, str], inp_groups: list[list[str]]
    ) -> tuple[list[str] | None, list[str] | None]:
        """Search for additional inputs (after the first)."""
        inp = sum(inp_groups, [])
        out = []
        for out_path in self.out:
            out_template = NoNamedTemplate(out_path)
            if not out_template.is_valid():
                raise ValueError(f"Invalid out template string in {self}: {out_path}")
            out.append(out_template.substitute(names))
        return inp, out

    def _comment_records(self, inp: list[str], out: list[str]) -> list[str]:
        """A few comments to be put before the build statements."""
        records = [f"command: {self.command.name}"]
        if inp is not None:
            records.append("inp: " + " ".join(inp))
        if out is not None and len(out) > 0:
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
                skip_record = self._skip_record(record)
                if skip_record is not None:
                    yield skip_record
                    continue
                if "outputs" not in record:
                    raise ValueError("Every build must have an output.")
                _override_variables(record, self.constants)
                _expand_constants(record, self.constants)
                _add_mkdir(record)
                _clean_build(record)
                if len(self.phony_deps) > 0:
                    record.setdefault("order_only", []).extend(self.phony_deps)
                yield record
                if self.default and record["rule"] != "phony":
                    yield record["outputs"]
            else:
                # defaults should not be present in command_records.
                raise NotImplementedError

    def _skip_record(self, build):
        """Skip build whose inputs are missing that are safe to ignore."""
        missing_inputs = []
        for inp in build.get("inputs", []) + build.get("implicit", []):
            ignore_safe = self.re_ignore_safe.fullmatch(inp) is not None
            if ignore_safe and not os.path.isfile(inp):
                missing_inputs.append(inp)
        if len(missing_inputs) > 0:
            return {
                "outputs": build["outputs"],
                "rule": "error",
                "variables": {"message": "Missing inputs: " + " ".join(missing_inputs)},
            }
        return None


def _test_filter_inp(inp) -> None | str:
    if "REPREPBUILD_FILTER_INP" not in os.environ:
        return None
    filter_inp = os.environ["REPREPBUILD_FILTER_INP"]
    if filter_inp not in inp:
        return f"Skipping records: REPREPBUILD_FILTER_INP={filter_inp} not in {inp}"
    return None


def _override_variables(build: dict, constants: dict[str, str]):
    variables = build.get("variables")
    if variables is not None:
        build["variables"] = {name: constants.get(name, value) for name, value in variables.items()}


def _expand_constants(build: dict, constants: dict[str, str]):
    """Expand constants and normalize paths in build record."""

    def _expand(path):
        path_template = CaseSensitiveTemplate(path)
        if not path_template.is_valid():
            raise ValueError(f"Invalid subsequent inp template string: {path}")
        path = path_template.substitute(constants)
        # TODO: Improve detection of path, or implement it differently.
        #       The current test may have false positives.
        if path.startswith(os.sep):
            path = os.path.normpath(os.path.relpath(path, constants["root"]))
        return path

    variables = build.get("variables")
    if variables is not None:
        build["variables"] = {name: _expand(path) for name, path in variables.items()}
    for key in "outputs", "inputs", "implicit", "order_only", "implicit_outputs":
        values = build.get(key)
        if values is not None:
            build[key] = [_expand(path) for path in values]
    depfile = build.get("depfile")
    if depfile is not None:
        build["depfile"] = _expand(depfile)


def _add_mkdir(build: dict):
    """Modify Ninja build record to include creation of output directories."""
    if build["rule"] == "phony":
        return
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
        pre_command = "mkdir -p " + " ".join(sorted(dirs_todo))
        _add_pre_commands(build, [pre_command])


def _add_pre_commands(build: dict, pre_commands: list[str]):
    variables = build.setdefault("variables", {})
    result = variables.get("_pre_command", "")
    result += "".join(f"{pre_command}; " for pre_command in pre_commands)
    variables["_pre_command"] = result


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
