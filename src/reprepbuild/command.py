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
"""RepRepBuild Commands are like generators, more specific and without glob args."""


import attrs

__all__ = ("Command",)


@attrs.define
class Command:
    @property
    def name(self) -> str:
        """The name of the command in ``reprepbuild.yaml``."""
        raise NotImplementedError

    @property
    def pools(self) -> dict[str, dict]:
        """A dict of (name, kwargs) for Ninja's ``Writer.pool()``."""
        return {}

    @property
    def rules(self) -> dict[str, dict]:
        """A dict of (name, kwargs) for Ninja's ``Writer.rule()``."""
        raise NotImplementedError

    def generate(self, inp: list[str], out: list[str], arg) -> tuple[list, list[str]]:
        """Generate records for ``build.ninja`` for the given inputs, outputs and arguments.

        Parameters
        ----------
        inp
            The input paths for the command.
        out
            The output paths for the command.
        arg
            Additional argument, may be anything.

        Returns
        -------
        records
            New records to be written to ``build.ninja`` for this command, using said
            inputs, outputs and arguments.
            A record can be a ``str`` (comment) or ``dict`` (build).
        gendeps
            A list of files that were read to compute the build records.
        """
        raise NotImplementedError
