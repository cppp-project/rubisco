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

"""Test rubisco.kernel.command_event.args module."""

import pytest

from rubisco.kernel.command_event.args import Option
from rubisco.lib.exceptions import RUTypeError, RUValueError


class TestOption:
    """Test rubisco.kernel.command_event.args.Option class."""

    def test_option(self) -> None:
        """Test rubisco.kernel.command_event.args.Option class."""
        opt = Option[str](
            name="name",
            title="title",
            description="desc",
            typecheck=str,
        )

        if opt.name != "name":
            pytest.fail("Option.name is not correct.")
        if opt.title != "title":
            pytest.fail("Option.title is not correct.")
        if opt.description != "desc":
            pytest.fail("Option.description is not correct.")
        if opt.typecheck is not str:
            pytest.fail("Option.typecheck is not correct.")

    def test_option_set(self) -> None:
        """Test rubisco.kernel.command_event.args.Option.set method."""
        opt = Option[str](
            name="name",
            title="title",
            description="desc",
            typecheck=str,
        )
        opt.set("value")
        if opt.value != "value":
            pytest.fail("Option.get is not correct.")

        opt.value = "value2"
        if opt.get() != "value2":
            pytest.fail("Option.get is not correct.")

        with pytest.raises(RUTypeError):
            opt.set(1)  # type: ignore[arg-type]

        with pytest.raises(RUTypeError):
            opt.value = 1  # type: ignore[assignment]

    def test_option_freeze(self) -> None:
        """Test rubisco.kernel.command_event.args.Option.freeze method."""
        opt = Option[str](
            name="name",
            title="title",
            description="desc",
            typecheck=str,
        )
        opt.freeze()
        with pytest.raises(RUValueError):
            opt.set("value")
        opt.unfreeze()
        opt.set("value")
        if opt.value != "value":
            pytest.fail("Option.get is not correct.")
