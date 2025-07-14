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

"""Rubisco command event router."""

from pathlib import PurePosixPath

from rubisco.kernel.command_event.cmd_event import EventObject
from rubisco.kernel.command_event.event_types import (
    EventObjectStat,
    EventObjectType,
)
from rubisco.kernel.command_event.root import set_root

# Set the root event.
set_root(
    EventObject(
        name="",
        parent=None,
        stat=EventObjectStat(
            type=EventObjectType.DIRECTORY,
            description="",
        ),
        abspath=PurePosixPath("/"),
    ),
)
