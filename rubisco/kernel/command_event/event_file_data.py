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

"""Rubisco event file data.

The event file data is a callback list and args list. It's used to store the
callbacks and args of a event file.
"""

from dataclasses import dataclass, field
from typing import Any, Self

from rubisco.kernel.command_event.args import Argument, DynamicArguments
from rubisco.kernel.command_event.callback import EventCallback
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.variable.fast_format_str import fast_format_str

__all__ = ["EventFileData"]


@dataclass
class EventFileData:
    """The data of an event file.

    It's contained args and callbacks.

    """

    args: list[Argument[Any]] | DynamicArguments = field(
        default_factory=list[Argument[Any]],
    )
    callbacks: list[EventCallback] = field(default_factory=list[EventCallback])

    def merge_callbacks(
        self,
        args: list[Argument[Any]] | DynamicArguments,
        callback: EventCallback,
    ) -> Self:
        """Merge the given args and callbacks to the current file data.

        Args:
            args (list[Argument[Any]] | DynamicArguments): The args to
                merge.
            callback (EventCallback): The callback to merge.

        Returns:
            Self: Self.

        The args of this file will be set to the given args if it's longer
        than the current args. The callbacks will be appended to the current
        callbacks.

        Don't merge the args that have different types at the same position.
        It will cause a `RUTypeError`.

        """
        if not self.args:
            self.args = args
            self.callbacks.append(callback)
            return self
        if not args:
            self.callbacks.append(callback)
            return self

        raise RUValueError(
            fast_format_str(
                _("Invalid args count of EventFileData: ${{ data }}"),
                fmt={"data": args},
            ),
        )

    def merge(self, data: "EventFileData") -> Self:
        """Merge the given args and callbacks to the current file data.

        Args:
            data (EventFileData): The file data to merge.

        Returns:
            Self: Self.

        The args of this file will be set to the given args if it's longer
        than the current args. The callbacks will be appended to the current
        callbacks.

        Don't merge the args that have different types at the same position.
        It will cause a `RUTypeError`.

        """
        for callback in data.callbacks:
            self.merge_callbacks(data.args, callback)

        return self
