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

from typing import TYPE_CHECKING, Any

from rubisco.cli.main.project_config import get_project_config
from rubisco.kernel.command_event.callback import EventCallback
from rubisco.kernel.command_event.event_file_data import EventFileData
from rubisco.kernel.command_event.event_path import EventPath
from rubisco.lib.l10n import _
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

if TYPE_CHECKING:
    from rubisco.kernel.command_event.args import Argument, Option

__all__ = ["register_builtin_cmds"]


def show_project_info(
    options: list[Option[Any]],  # noqa: ARG001 # pylint: disable=W0613
    args: list[Argument[Any]],  # noqa: ARG001 # pylint: disable=W0613
) -> None:
    """For 'rubisco info' command.

    Args:
        options (list[Option[Any]]): List of options.
        args (list[Argument[Any]]): List of arguments.

    """
    call_ktrigger(
        IKernelTrigger.on_show_project_info,
        project=get_project_config(),
    )


def register_builtin_cmds() -> None:
    """Register built-in commands."""
    # If user don't provide any arguments. We should show the project info.

    EventPath("/info").mkfile(
        EventFileData(
            callbacks=[
                EventCallback(
                    callback=show_project_info,
                    description=_(
                        "Default callback for showing Rubisco project infomation.",  # noqa: E501
                    ),
                ),
            ],
        ),
        description=_("Show project information."),
    )
