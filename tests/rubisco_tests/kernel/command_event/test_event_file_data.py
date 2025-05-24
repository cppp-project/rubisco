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

"""Test rubisco.kernel.command_event.event_file_data module."""


from typing import Any

import pytest

from rubisco.kernel.command_event.args import Argument, DynamicArguments, Option
from rubisco.kernel.command_event.callback import EventCallback
from rubisco.kernel.command_event.event_file_data import EventFileData
from rubisco.lib.exceptions import RUValueError


def _callback(
    options: list[Option[Any]],  # pylint: disable=W0613
    args: list[Argument[Any]],  # pylint: disable=W0613
) -> None:
    pass


cb = EventCallback(callback=_callback, description="desc")


def test_event_file_data() -> None:
    """Test EventFileData class."""
    dt = EventFileData()

    if dt.args != []:
        pytest.fail("Args should be empty.")

    if dt.callbacks != []:
        pytest.fail("Callbacks should be empty.")

    dt.merge(
        DynamicArguments[str](
            name="test",
            title="test",
            description="desc",
            mincount=0,
            maxcount=-1,
        ),
        cb,
    )

    with pytest.raises(RUValueError):
        dt.merge(
            DynamicArguments[str](
                name="test",
                title="test",
                description="desc",
                mincount=0,
                maxcount=-1,
            ),
            cb,
        )
