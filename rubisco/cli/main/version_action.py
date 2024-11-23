# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2024 The C++ Plus Project.
# This file is part of the Rubisco.
#
# Rubisco is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# Rubisco is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Utils for showing the version of the CLI."""

import argparse
from collections.abc import Sequence
from typing import Any

import rich

from rubisco.config import APP_NAME, APP_VERSION
from rubisco.lib.l10n import _

# ruff: noqa: D102 D107
# pylint: disable=missing-function-docstring

__all__ = ["CLIVersionAction", "show_version"]


def show_version() -> None:
    """Get version string."""
    rich.print(APP_NAME, f"[white]{APP_VERSION}[/white]", end="\n")

    copyright_text = _(
        "Copyright (C) 2024 The C++ Plus Project.\n"
        "License [bold]GPLv3+[/bold]: GNU GPL version [cyan]3[/cyan] or later "
        "<https://www.gnu.org/licenses/gpl.html>.\nThis is free "
        "software: you are free to change and redistribute it.\nThere is "
        "[yellow]NO WARRANTY[/yellow], to the extent permitted by law.\n"
        "Written by [underline]ChenPi11[/underline].",
    )

    rich.print(copyright_text)


class CLIVersionAction(argparse.Action):
    """Version Action for rubisco."""

    def __init__(  # pylint: disable=R0913, R0917
        self,
        option_strings: Sequence[str],
        version: str | None = None,
        dest: str = argparse.SUPPRESS,
        default: str = argparse.SUPPRESS,
        help: str | None = None,  # pylint: disable=W0622 # noqa: A002
    ) -> None:
        if help is None:
            help = _(  # pylint: disable=W0622 # noqa: A001
                "Show program's version number and exit.",
            )
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help,
        )
        self.version = version

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,  # noqa: ARG002
        values: str | Sequence[Any] | None,  # noqa: ARG002
        option_string: str | None = None,  # noqa: ARG002
    ) -> None:
        show_version()
        parser.exit()
