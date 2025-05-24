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


from typing import Any, TypeVar, cast

from rubisco.lib.variable import to_autotype
from rubisco.lib.variable.autoformatdict import AFTypeError, AutoFormatDict
from rubisco.lib.variable.autoformatlist import AutoFormatList
from rubisco.lib.variable.builtin_vars import init_builtin_vars
from rubisco.lib.variable.callbacks import add_undefined_var_callback
from rubisco.lib.variable.format import format_str
from rubisco.lib.variable.utils import (
    assert_iter_types,
    iter_assert,
    make_pretty,
)
from rubisco.lib.variable.variable import (
    get_variable,
    pop_variables,
    push_variables,
    variables,
)

__all__ = [
    "AFTypeError",
    "AutoFormatDict",
    "AutoFormatList",
    "add_undefined_var_callback",
    "assert_iter_types",
    "format_str",
    "get_variable",
    "iter_assert",
    "make_pretty",
    "pop_variables",
    "push_variables",
    "variables",
]


T = TypeVar("T")
KT = TypeVar("KT")
VT = TypeVar("VT")


def _to_autotype(
    obj: T | list[VT] | dict[str, Any],
) -> T | AutoFormatList[VT] | AutoFormatDict:
    """Convert the list or dict object to AutoFormatList or AutoFormatDict.

    If not list or dict, return itself.
    """
    if isinstance(obj, dict) and not isinstance(obj, AutoFormatDict):
        return AutoFormatDict(obj)
    if isinstance(obj, list) and not isinstance(obj, AutoFormatList):
        return AutoFormatList(cast("list[VT]", obj))

    return cast("T", obj)


to_autotype.set_to_autotype_func(_to_autotype)


init_builtin_vars()
