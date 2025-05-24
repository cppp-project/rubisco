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

"""Test rubisco.lib.variable.var_container module."""

import pytest

from rubisco.lib.variable.var_container import VariableContainer
from rubisco.lib.variable.variable import get_variable, has_variable


class TestVariableContainer:
    """Test the VariableContainer class."""

    def test_variable_container(self) -> None:
        """Test the VariableContainer class."""
        fmt = {"var1": "value1", "var2": "value2"}
        with VariableContainer(fmt):
            if get_variable("var1") != "value1":
                pytest.fail("var1 is not set correctly.")
            if get_variable("var2") != "value2":
                pytest.fail("var2 is not set correctly.")

        if has_variable("var1") or has_variable("var2"):
            pytest.fail("Variables should be removed after context exit.")

    def test_variable_container_empty(self) -> None:
        """Test the VariableContainer class with empty format dictionary."""
        with VariableContainer():
            pass

    def test_variable_container_none(self) -> None:
        """Test the VariableContainer class with None format dictionary."""
        with VariableContainer(None):
            pass
