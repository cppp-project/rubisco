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

"""Test rubisco.lib.variable.format module."""

import pytest

from rubisco.lib.variable.format import format_str
from rubisco.lib.variable.variable import variables


class TestFormatStr:
    """Test format_str."""

    def _reset(self) -> None:
        variables.clear()

    def test_empty(self) -> None:
        """Test empty string."""
        self._reset()
        if format_str("") != "":
            pytest.fail("format_str() should return empty string")

    def test_no_var(self) -> None:
        """Test no variable."""
        self._reset()
        if format_str("hello") != "hello":
            pytest.fail("format_str() should return the same string")

    def test_var(self) -> None:
        """Test variable."""
        self._reset()
        if format_str("hello ${{var}}", fmt={"var": "world"}) != "hello world":
            pytest.fail("format_str() should return the formatted string")

    def test_var_with_decoration(self) -> None:
        """Test variable with decoration."""
        self._reset()
        if format_str("hello ${{var:1}}") != "hello 1":
            pytest.fail("format_str() should return the formatted string")

    def test_var_with_pyexpr(self) -> None:
        """Test variable with python expression."""
        self._reset()
        if format_str("hello ${{var:$&{{1+1}}}}}}") != "hello 2}}":
            pytest.fail("format_str() should return the formatted string")
