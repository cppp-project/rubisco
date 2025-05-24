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

"""Test rubisco.shared.ktrigger module."""

from contextlib import suppress
from typing import Any

import pytest

from rubisco.lib.exceptions import RUValueError
from rubisco.shared.ktrigger import (
    IKernelTrigger,
    bind_ktrigger_interface,
    call_ktrigger,
)


class TestKrigger:
    """Test KTrigger."""

    class _TestKTrigger(IKernelTrigger):
        _prog_total: int | float
        _prog_current: int | float

        def on_test0(self) -> None:
            """Test0: KTrigger without arguments."""

        def on_test1(self, arg1: str, arg2: str) -> None:
            """Test1: KTrigger with two arguments."""
            if arg1 != "Linus" or arg2 != "Torvalds":
                raise AssertionError

        def on_test2(self, **kwargs: dict[str, Any]) -> None:
            """Test2: KTrigger with *args and **kwargs."""
            if kwargs != {
                "gnu": "Stallman",
                "nividia": "F**k",
            }:
                raise AssertionError

        def on_test3(self) -> None:
            """Test3: KTrigger raises an exception."""
            msg = "Test3 exception."
            raise ValueError(msg)

    @classmethod
    def setup_class(cls) -> None:
        """Init test suites."""
        cls.kt = cls._TestKTrigger()
        bind_ktrigger_interface("test", cls.kt)

    def test_same_name_ktrigger(self) -> None:
        """Test binding a KTrigger with the same sign."""
        pytest.raises(RUValueError, bind_ktrigger_interface, "test", self.kt)

    def test_call_ktrigger(self) -> None:
        """Test calling a KTrigger."""
        call_ktrigger("on_test0")
        call_ktrigger("on_test1", arg1="Linus", arg2="Torvalds")
        call_ktrigger(
            "on_test2",
            gnu="Stallman",
            nividia="F**k",
        )
        with suppress(ValueError):
            call_ktrigger("on_test3")

    def test_non_exists_krigger(self) -> None:
        """Test calling a non-exists KTrigger."""
        call_ktrigger("non_exists")
