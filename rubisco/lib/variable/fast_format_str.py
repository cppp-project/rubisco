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

"""Format a string that only contains literal text and simple variables.

The simple variables is a expression that only contains ${{var}} without
python expression or decoration.

e.g. "Hello ${{name}}!" is a simple variable expression."
Because the expression only contains literal text and simple variable without
decoration, it can be formatted with str.replace().
It is faster than the full format_str() function.
"""

import re
from typing import Any

import pytest

from rubisco.lib.exceptions import RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.variable.var_contianer import VariableContainer
from rubisco.lib.variable.variable import get_variable, push_variables

__all__ = ["fast_format_str"]


def fast_format_str(
    string: str | Any,  # noqa: ANN401
    *,
    fmt: dict[str, Any] | None = None,
) -> str | Any:  # noqa: ANN401
    """Format the string with variables.

    Args:
        string (str): The string to format.
        fmt (dict[str, Any] | None): The format dictionary.
            Defaults to None.

    Returns:
        str: The formatted string. If the input is not a string,
            return itself.

    Raises:
        RUValueError: If the string contains a variable expression
            that is not a simple variable expression.

    """
    if not isinstance(string, str):
        return string

    if re.search(r"\$\&\{\{.*\}\}", string):
        msg = _("fast_format_str() only supports simple variable expressions.")
        raise RUValueError(
            msg,
        )

    if re.search(r"\$\{\{.*\:.*\}\}", string):
        msg = _("fast_format_str() does not support default value.")
        raise RUValueError(
            msg,
        )

    matches = re.finditer(
        r"\$\{\{\s*[a-zA-Z_][a-zA-Z0-9_.-]*\s*\}\}",
        string,
    )

    if not matches:
        return string

    with VariableContainer(fmt):
        # If the string only contains a variable, return the variable value
        # without converting to a string.
        m = re.match(r"^\$\{\{\s*[a-zA-Z_][a-zA-Z0-9_.-]*\s*\}\}$", string)
        if m:
            varname = m.group()[3:-2].strip()
            return get_variable(varname)

        for match in matches:
            varname = match.group()[3:-2].strip()
            val = get_variable(varname)
            string = string.replace(match.group(), str(val))
    return string


class TestFastFormatStr:
    """Test fast_format_str."""

    def test_empty(self) -> None:
        """Test empty string."""
        if fast_format_str("") != "":
            raise AssertionError

    def test_literal(self) -> None:
        """Test literal string."""
        if fast_format_str("hello") != "hello":
            raise AssertionError

    def test_var(self) -> None:
        """Test variable."""
        push_variables("var", "world")
        if fast_format_str("${{var}}") != "world":
            raise AssertionError
        push_variables("var", 1)
        if fast_format_str("${{var}}") != 1:
            raise AssertionError
        if fast_format_str("${{var}}", fmt={"var": "test"}) != "test":
            raise AssertionError
        if fast_format_str("${{var}}", fmt={"var": 0.0}) != 0.0:
            raise AssertionError

    def test_var_not_found(self) -> None:
        """Test variable not found."""
        pytest.raises(
            KeyError,
            fast_format_str,
            "${{_U}}",
        )

    def test_var_name(self) -> None:
        """Test variable name."""
        fast_format_str("${{   s s }}")
        if (
            fast_format_str(
                "${{  a}} ${{ a_b   }} ${{a-b}} ${{a.b}}",
                fmt={"a": 1, "a_b": 2, "a-b": 3, "a.b": 4},
            )
            != "1 2 3 4"
        ):
            raise AssertionError

    def test_var_with_decoration(self) -> None:
        """Test variable with decoration."""
        pytest.raises(
            RUValueError,
            fast_format_str,
            "${{var:1}}",
        )

    def test_var_with_pyexpr(self) -> None:
        """Test variable with python expression."""
        pytest.raises(
            RUValueError,
            fast_format_str,
            "${{var:$&{{1+1}}}}",
        )
