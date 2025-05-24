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

from typing import Any, TypeVar

from rubisco.lib.variable.execute import execute_expression
from rubisco.lib.variable.lexer import get_token
from rubisco.lib.variable.ru_ast import parse_expression
from rubisco.lib.variable.var_container import VariableContainer

__all__ = ["format_str"]


T = TypeVar("T")


def format_str(
    string: T,
    *,
    fmt: dict[str, Any] | None = None,
) -> T | Any:  # noqa: ANN401
    """Format the string with variables.

    Args:
        string (T): The string to format.
        fmt (dict[str, Any] | None): The format dictionary.
            Defaults to None.

    Returns:
        T | Any: The formatted string. If the input is not a string,
            return itself.

    """
    if not isinstance(string, str):
        return string

    with VariableContainer(fmt):
        return execute_expression(parse_expression(get_token(string)))
