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

"""Test rubisco.lib.variable.variable module."""

import pytest

from rubisco.lib.variable.variable import (
    get_variable,
    has_variable,
    pop_variables,
    push_variables,
    variables,
)


class TestVariable:
    """Test variable system."""

    def _reset(self) -> None:
        variables.clear()

    def test_push_pop_variables(self) -> None:
        """Test push and pop variables."""
        self._reset()
        push_variables("a", 1)
        if get_variable("a") != 1:
            pytest.fail("Variable a should be 1")

        push_variables("a", "x")
        if get_variable("a") != "x":
            pytest.fail("Variable a should be x")

        if has_variable("a") is False:
            pytest.fail("Variable a should exist")

        if pop_variables("a") != "x":
            pytest.fail("Variable a should be x")
        if get_variable("a") != 1:
            pytest.fail("Variable a should be 1")

        if pop_variables("a") != 1:
            pytest.fail("Variable a should be 1")

        if has_variable("a") is True:
            pytest.fail("Variable a should not exist")

        pytest.raises(KeyError, get_variable, "a")

    def test_push_pop_variables_default(self) -> None:
        """Test push and pop variables with default value."""
        self._reset()
        if pop_variables("a", default=1) != 1:
            pytest.fail("Variable a should be 1.")

        push_variables("a", 1)
        if pop_variables("a", default=2) != 1:
            pytest.fail("Variable a should be 1.")
