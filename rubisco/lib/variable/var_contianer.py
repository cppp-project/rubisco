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

"""A variable container.

This module provides a context manager for variable substitution in strings.
It allows for the temporary replacement of variables in a string with
their corresponding values from a dictionary. Restoring the
original values when the context is exited.
"""

from types import TracebackType
from typing import Any

from rubisco.lib.variable.variable import (
    get_variable,
    has_variable,
    pop_variables,
    push_variables,
)

__all__ = ["VariableContainer"]


class VariableContainer:
    """The variable container."""

    def __init__(self, fmt: dict[str, Any] | None = None) -> None:
        """Initialize the variable container.

        Args:
            fmt (dict[str, Any] | None): The format dictionary.
                Defaults to None.

        """
        self._fmt = fmt or {}

    def __enter__(self) -> "VariableContainer":
        """Enter the variable container.

        Returns:
            VariableContainer: The variable container.

        """
        for key, value in self._fmt.items():
            push_variables(key, value)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Exit the variable container.

        Args:
            exc_type (Any): The exception type.
            exc_value (Any): The exception value.
            traceback (Any): The traceback.

        """
        for key in self._fmt:
            pop_variables(key)


class TestVariableContainer:
    """Test the VariableContainer class."""

    def test_variable_container(self) -> None:
        """Test the VariableContainer class."""
        fmt = {"var1": "value1", "var2": "value2"}
        with VariableContainer(fmt):
            if get_variable("var1") != "value1":
                raise AssertionError
            if get_variable("var2") != "value2":
                raise AssertionError

        if has_variable("var1") or has_variable("var2"):
            raise AssertionError

    def test_variable_container_empty(self) -> None:
        """Test the VariableContainer class with empty format dictionary."""
        with VariableContainer():
            pass

    def test_variable_container_none(self) -> None:
        """Test the VariableContainer class with None format dictionary."""
        with VariableContainer(None):
            pass
