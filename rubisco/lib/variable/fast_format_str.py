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

from rubisco.lib.exceptions import RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.variable.var_container import VariableContainer
from rubisco.lib.variable.variable import get_variable

__all__ = ["fast_format_str"]


def fast_format_str(
    string: str | Any,  # noqa: ANN401
    *,
    fmt: dict[str, Any] | None = None,
) -> str | Any:  # noqa: ANN401
    """Format the string with variables.

    This function is faster than the full format_str() function.
    It only supports literal text and simple variables without decoration.
    It's not recommended to use this function to format a string that from
    user input. Suggest to use this function when formatting a message.

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
            Although "${{var:${{var}}}} : ${{var}}" is a expression with
            decoration, but safety check will not raise an error.
            This is a bug, but I don't want to fix it. (We need fast instead of
            100% safety)
            If someday this project is rewritten in some other faster language
            (never be Rust), this function will be deprecated.

    """
    if not isinstance(string, str):
        return string

    if re.search(r"\$\&\{\{.*\}\}", string):
        msg = _("fast_format_str() only supports simple variable expressions.")
        raise RUValueError(
            msg,
        )

    if re.search(r"\$\{\{([^{}]+?):([^{}]+?)\}\}", string):
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
