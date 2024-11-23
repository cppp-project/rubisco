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

"""Help formatter for CLI."""

import argparse
from collections.abc import Iterable

from rich_argparse import RichHelpFormatter

from rubisco.lib.l10n import _

# ruff: noqa: D102 D107
# pylint: disable=missing-function-docstring

__all__ = ["RUHelpFormatter"]


class RUHelpFormatter(RichHelpFormatter):
    """Rubisco CLI help formatter."""

    def add_usage(
        self,
        usage: str | None,
        actions: Iterable[argparse.Action],
        groups: Iterable[argparse._MutuallyExclusiveGroup],
        prefix: str | None = None,
    ) -> None:
        for action in actions:
            if action.help == "show this help message and exit":
                action.help = _("Show this help message and exit.")

        super().add_usage(usage, actions, groups, prefix)

    def format_help(self) -> str:
        help_str = super().format_help()
        help_str = help_str.replace("Usage:", _("Usage:"))
        help_str = help_str.replace(
            "Positional Arguments:",
            _("Positional Arguments:"),
        )

        return help_str.replace("Options:", _("Options:"))
