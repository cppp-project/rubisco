# -*- coding: utf-8 -*-
# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2024 The C++ Plus Project.
# This file is part of the cppp-repoutils.
#
# cppp-repoutils is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# cppp-repoutils is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
cppp-repoutils variable system.
"""

from typing import Any, overload

from cppp_repoutils.utils.stack import Stack
from cppp_repoutils.utils.nls import _

__all__ = [
    "variables",
    "push_variables",
    "pop_variables",
    "get_variable",
    "format_str",
    "AutoFormatDict",
]

# The global variable container.
variables: dict[str, Stack] = {}


def push_variables(name, value: str) -> None:
    """Push a new variable.

    Args:
        name (str): The name of the variable.
        value (str): The value of the variable.
    """

    if name in variables:
        variables[name].push(value)
    else:
        variables[name] = Stack()
        variables[name].push(value)


def pop_variables(name: str) -> None:
    """Pop the top value of the given variable.

    Args:
        name (str): The name of the variable.

    Returns:
        str: The top value of the given variable.
    """

    if name in variables:
        return variables[name].pop()
    return None


def get_variable(name: str) -> None:
    """Get the value of the given variable.

    Args:
        name (str): The name of the variable.

    Returns:
        str: The value of the given variable.
    """

    if name in variables:
        return variables[name].top()
    raise KeyError(repr(name))


def format_str(
    string: str | Any, fmt: dict[str, str] | None = None  # noqa: E501
) -> str | Any:
    """Format the string with variables.

    Args:
        string (str | Any): The string to format.

    Returns:
        str | Any: The formatted string. If the input is not a string,
            return itself.
    """

    if not isinstance(string, str):
        return string

    if fmt is None:
        fmt = {}

    for key, val in fmt.items():  # Ignore unused and unformatted keys.
        string = string.replace(f"{{{key}}}", str(val))

    for name, values in variables.items():
        string = string.replace(f"{{{name}}}", values.top())  # {name} -> value

    return string


class AutoFormatDict(dict):
    """A dictionary that can format value automatically with variables."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize AutoFormatDict."""

        super().__init__(*args, **kwargs)

    @overload
    def get(self, key: str) -> str | Any:
        """Get the value of the given key.

        Args:
            key (str): The key to get value.

        Returns:
            str | Any: The value of the given key.

        Raises:
            KeyError: If the key is not in the dict.
        """

    @overload
    def get(self, key: str, default: str | Any) -> str | Any:
        """Get the value of the given key.

        Args:
            key (str): The key to get value.
            default (str | Any): The default value.

        Returns:
            str | Any: The value of the given key.
        """

    @overload
    def get(self, key: str, valtype: type) -> str | Any:
        """Get the value of the given key.

        Args:
            key (str): The key to get value.
            valtype (type): The type of the value. If it is not None, we will
                check the type of the value.

        Returns:
            str | Any: The value of the given key.

        Raises:
            TypeError: If the type of the value is not the same as the given
                type.
        """

    @overload
    def get(self, key: str, default: str | Any, valtype: type) -> str | Any:
        """Get the value of the given key.

        Args:
            key (str): The key to get value.
            default (str | Any): The default value.
            valtype (type): The type of the value. If it is not None, we will
                check the type of the value.

        Returns:
            str | Any: The value of the given key.

        Raises:
            TypeError: If the type of the value is not the same as the given
                type.
        """

    def get(self, key: str, *args, **kwargs) -> str | Any:
        res: str | Any
        if key not in self.keys() and len(args) == 0:
            raise KeyError(key)
        if key not in self.keys() and len(args) == 1:
            res = format_str(args[0])
        else:
            res = format_str(super().get(key))
        typecheck = kwargs.get("valtype", object)
        if len(args) == 2:
            typecheck = args[1]

        if isinstance(typecheck, type) and not isinstance(res, typecheck):
            vtype = type(res)
            if vtype == AutoFormatDict:
                vtype = dict  # Make it more readable.
            raise TypeError(
                _(
                    "The value of key {key} needs to be {type} instead of {vtype}",  # noqa: E501
                ).format(
                    key=repr(key),
                    type=repr(typecheck.__name__),
                    vtype=repr(vtype.__name__),
                )
            )

        return res

    def __setitem__(self, key: str, value: str | Any) -> None:
        """Set the value of the given key.

        Args:
            key (str): The key to set value.
            value (str | Any): The value to set.
        """

        if isinstance(value, str):
            value = format_str(value)
        super().__setitem__(key, AutoFormatDict.from_dict(value))

    def __getitem__(self, key: str) -> str | Any:
        """Get the value of the given key.

        Args:
            key (str): The key to get value.

        Returns:
            str | Any: The value of the given key.
        """

        return self.get(key)

    def __repr__(self, *args, **kwargs) -> str:
        """Return the representation of the AutoFormatDict.

        Returns:
            str: The representation of the AutoFormatDict.
        """

        return f"{type(self).__name__}({super().__repr__(*args, **kwargs)})"

    @staticmethod
    def from_dict(srcdict: dict[str, Any] | Any) -> "AutoFormatDict":
        """Create a AutoFormatDict from the given dict recursively.

        Args:
            src (dict[str, Any]): The dict to create AutoFormatDict. If it is
                not a dict, return it directly.

        Returns:
            AutoFormatDict: The created AutoFormatDict.
        """

        if isinstance(srcdict, dict):
            srcdict = srcdict.copy()

        return convert_to_afd(srcdict)


def convert_to_afd(src: dict[str, Any] | Any) -> AutoFormatDict | Any:
    """Convert the given dict to AutoFormatDict recursively.

    Args:
        src (dict[str, Any] | Any): The dict to convert. If it is not a dict,
            return it directly.

    Returns:
        AutoFormatDict | Any: The converted AutoFormatDict.
    """

    if isinstance(src, list | tuple | set):
        tmp_src = list(src)
        for index, value in enumerate(tmp_src):
            tmp_src[index] = convert_to_afd(value)
        src = type(src)(tmp_src)
    elif isinstance(src, dict):
        for key, value in src.items():
            if isinstance(value, list | tuple | set | dict):
                src[key] = convert_to_afd(value)
                src.update(src)

        afdict = AutoFormatDict()
        for key, value in src.items():
            afdict[key] = value
        src = afdict

    return src
