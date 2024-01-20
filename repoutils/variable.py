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

from typing import Any

from repoutils.stack import Stack

__all__ = [
    "variables",
    "push_variables",
    "pop_variables",
    "get_variable",
    "format_string_with_variables",
    "AutoFormatDict",
]

# The global variable container.
variables: dict[str, Stack] = {}


def push_variables(name, value: str):
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


def pop_variables(name: str):
    """Pop the top value of the given variable.

    Args:
        name (str): The name of the variable.

    Returns:
        str: The top value of the given variable.
    """

    if name in variables:
        return variables[name].pop()
    return None


def get_variable(name: str):
    """Get the value of the given variable.

    Args:
        name (str): The name of the variable.

    Returns:
        str: The value of the given variable.
    """

    if name in variables:
        return variables[name].top()
    raise KeyError(repr(name))


# This function ignores unused and unformatted variables.
def _format(message: str, fmt: dict[str, str] = None):
    if fmt is None:
        fmt = {}
    for key, val in fmt.items():
        message = message.replace(f"{{{key}}}", str(val))
    return message


def format_string_with_variables(string: str, fmt: dict[str, str] = None):
    """Format the string with variables.

    Args:
        string (str): The string to format.

    Returns:
        str: The formatted string.
    """

    if not isinstance(string, str):
        return string

    if fmt is None:
        fmt = {}

    string = _format(string, fmt)

    for name, values in variables.items():
        string = string.replace("{" + name + "}", values.top())  # {name} -> value

    return string


class AutoFormatDict(dict):
    """A dictionary that can format value automatically with variables."""

    def __init__(self, *args, **kwargs):
        """Initialize AutoFormatDict."""

        super().__init__(*args, **kwargs)

    def get(self, key: str, *args):
        """Get the value of the given key.

        Args:
            key (str): The key to get value.
            default (str): The default value.

        Returns:
            str: The value of the given key.
        """

        if not key in self.keys() and len(args) == 0:
            raise KeyError(repr(key))
        if not key in self.keys() and len(args) == 1:
            return format_string_with_variables(args[0])
        return format_string_with_variables(super().get(key))

    def __getitem__(self, key: str):
        """Get the value of the given key.

        Args:
            key (str): The key to get value.

        Returns:
            str: The value of the given key.
        """

        return self.get(key)

    @staticmethod
    def from_dict(srcdict: dict[str, Any]):
        """Create a AutoFormatDict from the given dict.

        Args:
            src (dict[str, Any]): The dict to create AutoFormatDict.

        Returns:
            AutoFormatDict: The created AutoFormatDict.
        """

        afdict = AutoFormatDict()
        for key, value in srcdict.items():
            afdict[key] = value
        return afdict
