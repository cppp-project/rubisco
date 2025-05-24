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

"""Rubisco command event types."""

import enum
from dataclasses import dataclass, field
from os import PathLike
from pathlib import PurePath
from typing import Any

from rubisco.kernel.command_event.args import Option
from rubisco.kernel.command_event.callback import EventCallbackFunction


class EventObjectType(enum.Enum):
    """The type of an command event tree node."""

    # It's like subparser in argparse. Contains subcommands.
    DIRECTORY = enum.auto()
    # It's like a command in argparse. This is a callable command event.
    FILE = enum.auto()
    # Alias for a command event.
    ALIAS = enum.auto()
    # Mount point for a command event. It can be import a external command event
    # in system path.
    MOUNT_POINT = enum.auto()


@dataclass
class EventObjectStat:
    """The stat of an command event tree node."""

    # The type of an command event tree node.
    type: EventObjectType

    # Attributes for directory, file and mount point.
    options: list[Option[Any]] = field(
        default_factory=list[Option[Any]],
    )

    # Attributes for directory.
    dir_description: str | None = None
    dir_callbacks: list[EventCallbackFunction] = field(
        default_factory=list[EventCallbackFunction],
    )

    # Attributes for alias.
    alias_to: PurePath | PathLike[str] | str | None = None

    def __post_init__(self) -> None:
        """Post init."""
        self.alias_to = PurePath(self.alias_to) if self.alias_to else None
        if self.type == EventObjectType.ALIAS and self.alias_to is None:
            msg = "Alias must have an alias_to."
            raise ValueError(msg)
