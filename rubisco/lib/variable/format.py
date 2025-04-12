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

"""Rubisco string formatter with variable."""

from typing import TypeVar

from rubisco.lib.variable.execute import execute_expression
from rubisco.lib.variable.lexer import get_token
from rubisco.lib.variable.ru_ast import parse_expression
from rubisco.lib.variable.var_contianer import VariableContainer

__all__ = ["format_str"]


T = TypeVar("T")

def format_str(
    string: str | T,
    *,
    fmt: dict[str, str] | None = None,
) -> str | T:
    """Format the string with variables.

    Args:
        string (str | T): The string to format.
        fmt (dict[str, str] | None): The format dictionary.
            Defaults to None.

    Returns:
        str | T: The formatted string. If the input is not a string,
            return itself.

    """
    if not isinstance(string, str):
        return string

    with VariableContainer(fmt):
        return execute_expression(parse_expression(get_token(string)))


class TestFormatStr:
    """Test format_str."""

    def test_empty(self) -> None:
        """Test empty string."""
        if format_str("") != "":
            raise AssertionError

    def test_no_var(self) -> None:
        """Test no variable."""
        if format_str("hello") != "hello":
            raise AssertionError

    def test_var(self) -> None:
        """Test variable."""
        if format_str("hello ${{var}}", fmt={"var": "world"}) != "hello world":
            raise AssertionError

    def test_var_with_decoration(self) -> None:
        """Test variable with decoration."""
        if format_str("hello ${{var:1}}") != "hello 1":
            raise AssertionError

    def test_var_with_pyexpr(self) -> None:
        """Test variable with python expression."""
        if format_str("hello ${{var:$&{{1+1}}}}}}")!= "hello 2}}":
            raise AssertionError
