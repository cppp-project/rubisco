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

"""Rubisco variable system."""

from typing import Any

from rubisco.lib.stack import Stack
from rubisco.lib.variable import (
    AutoFormatDict,
    AutoFormatList,
    add_undefined_var_callback,
    assert_iter_types,
    format_str,
    get_variable,
    iter_assert,
    make_pretty,
    pop_variables,
    push_variables,
)
from rubisco.lib.variable import (
    variables as _variables,
)
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.variable.var_container import VariableContainer

__all__ = [
    "AutoFormatDict",
    "AutoFormatList",
    "VariableContainer",
    "add_undefined_var_callback",
    "assert_iter_types",
    "fast_format_str",
    "format_str",
    "get_orig_variables",
    "get_variable",
    "get_variables",
    "get_variables",
    "iter_assert",
    "make_pretty",
    "pop_variables",
    "push_variables",
]


def get_orig_variables() -> dict[str, Stack[Any]]:
    """Get original variables list with stack info.

    Warning:
        This function will return the original variables list, if you update
        the returned dictionary, it will update the original variables list.

    Returns:
        dict[str, Stack[Any]]: The original variables list with stack info.

    """
    return _variables


def get_variables() -> dict[str, Any]:
    """Get variables list.

    Returns:
        dict[str, Any]: The variables list.

    """
    return {k: v.top() for k, v in _variables.items()}
