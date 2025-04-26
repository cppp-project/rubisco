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

"""C++ Plus Rubisco built-in command lines."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rubisco.cli.main.arg_parser import arg_parser, commands_parser
from rubisco.cli.main.help_formatter import RUHelpFormatter
from rubisco.cli.main.project_config import get_project_config
from rubisco.cli.main.version_action import show_version
from rubisco.lib.l10n import _
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

if TYPE_CHECKING:
    from argparse import Namespace

__all__ = ["register_builtin_cmds"]


def show_project_info(_: Namespace) -> None:
    """For 'rubisco info' command."""
    call_ktrigger(
        IKernelTrigger.on_show_project_info,
        project=get_project_config(),
    )


def _show_version(_: Namespace) -> None:
    show_version()


def register_builtin_cmds() -> None:
    """Register built-in commands."""
    # If user don't provide any arguments. We should show the project info.
    arg_parser.set_defaults(func=show_project_info)

    # For "rubisco info" command.
    commands_parser.add_parser(
        "info",
        help=_("Show project information."),
        formatter_class=RUHelpFormatter,
    ).set_defaults(func=show_project_info)

    # For "rubisco version" command.
    commands_parser.add_parser(
        "version",
        help=_("Show Rubisco version."),
        formatter_class=RUHelpFormatter,
    ).set_defaults(func=_show_version)
