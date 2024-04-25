# -*- coding: utf-8 -*-
# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2024 The C++ Plus Project.
# This file is part of the repoutils.
#
# repoutils is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# repoutils is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Repoutils variable system.
"""

import os
import sys
from pathlib import Path
from platform import uname
from queue import Empty, LifoQueue
from time import monotonic as time
from typing import Any, overload

from repoutils.constants import APP_VERSION, REPOUTILS_COMMAND
from repoutils.lib.l10n import _

__all__ = [
    "variables",
    "push_variables",
    "pop_variables",
    "get_variable",
    "format_str",
    "AutoFormatDict",
]


class Stack(LifoQueue):
    """A LifoQueue that can get the top value."""

    def top(self, block: bool = True, timeout: int | None = None) -> Any:
        """Get the top value of the stack.

        Args:
            block (bool): If it is True, block until an item is available.
            timeout (int | None): If it is positive, block at most timeout
                seconds.

        Returns:
            Any: The top value of the stack.
        """

        with self.not_empty:
            if not block:
                if not self._qsize():
                    raise Empty
            elif timeout is None:
                while not self._qsize():
                    self.not_empty.wait()
            elif timeout < 0:
                raise ValueError("'timeout' must be a non-negative number")
            else:
                endtime = time() + timeout
                while not self._qsize():
                    remaining = endtime - time()
                    if remaining <= 0.0:
                        raise Empty
                    self.not_empty.wait(remaining)
            item = self.queue[-1]
            return item

    def top_nowait(self) -> Any:
        """Get the top value of the stack without blocking.

        Returns:
            Any: The top value of the stack.
        """

        return self.top(False)

    def __str__(self) -> str:
        """Get the string representation of the stack.

        Returns:
            The string representation of the stack.
        """

        return self.__repr__()

    def __repr__(self) -> str:
        """Get the string representation of the stack.

        Returns:
            The string representation of the stack.
        """

        return f"[{', '.join([repr(item) for item in self.queue])}>"


# The global variable container.
variables: dict[str, Stack] = {}


def push_variables(name, value: str) -> None:
    """Push a new variable.

    Args:
        name (str): The name of the variable.
        value (str): The value of the variable.
    """

    if name in variables:
        variables[name].put(value)
    else:
        variables[name] = Stack()
        variables[name].put(value)


def pop_variables(name: str) -> None:
    """Pop the top value of the given variable.

    Args:
        name (str): The name of the variable.

    Returns:
        str: The top value of the given variable.
    """

    if name in variables:
        return variables[name].get()
    return None


def get_variable(name: str) -> Any:
    """Get the value of the given variable.

    Args:
        name (str): The name of the variable.

    Returns:
        Any: The value of the given variable.
    """

    if name in variables:
        return variables[name].top()
    raise KeyError(repr(name))


uname_result = uname()

# Built-in variables.
push_variables("home", str(Path.home().absolute()))
push_variables("cwd", str(Path.cwd().absolute()))
push_variables("repoutils_version", str(APP_VERSION))
push_variables("repoutils_command", str(REPOUTILS_COMMAND))
push_variables("host_os", os.name)
push_variables("host_system", uname_result.system)
push_variables("host_node", uname_result.node)
push_variables("host_release", uname_result.release)
push_variables("host_version", uname_result.version)
push_variables("host_machine", uname_result.machine)
push_variables("host_processor", uname_result.processor)
push_variables("repoutils_python_version", sys.version)
push_variables("repoutils_python_implementation", sys.implementation.name)
# Built-in variables for colorized output. Default to empty string.
# UCI (User Control Interface) can replace them.
push_variables("red", "")
push_variables("yellow", "")
push_variables("green", "")
push_variables("cyan", "")
push_variables("blue", "")
push_variables("magenta", "")
push_variables("gray", "")
push_variables("white", "")
push_variables("reset", "")
push_variables("bold", "")
push_variables("underline", "")
push_variables("blink", "")
push_variables("reverse", "")
push_variables("hidden", "")
push_variables("italic", "")


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
    def get(self, key: str) -> Any:
        """Get the value of the given key.

        Args:
            key (str): The key to get value.

        Returns:
            Any: The value of the given key.

        Raises:
            KeyError: If the key is not in the dict.
        """

    @overload
    def get(self, key: str, default: Any) -> Any:
        """Get the value of the given key.

        Args:
            key (str): The key to get value.
            default (Any): The default value.

        Returns:
            Any: The value of the given key.
        """

    @overload
    def get(self, key: str, valtype: type) -> Any:
        """Get the value of the given key.

        Args:
            key (str): The key to get value.
            valtype (type): The type of the value. If it is not None, we will
                check the type of the value.

        Returns:
            Any: The value of the given key.

        Raises:
            RUValueException: If the type of the value is not the same as the
                given type.
        """

    @overload
    def get(self, key: str, default: Any, valtype: type) -> Any:
        """Get the value of the given key.

        Args:
            key (str): The key to get value.
            default (Any): The default value.
            valtype (type): The type of the value. If it is not None, we will
                check the type of the value.

        Returns:
            Any: The value of the given key.

        Raises:
            RUValueException: If the type of the value is not the same as the
                given type.
        """

    def get(self, key: str, *args, **kwargs) -> Any:
        res: Any
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
            # This exception need hint, but we can't use the RUValueException.
            # Because it may cause circular import. So we use ValueError
            # instead.
            exc = ValueError(
                format_str(
                    _(
                        "The value of key {key} needs to be {type} instead of "
                        "{value_type}.",
                    ),
                    fmt={
                        "key": repr(key),
                        "type": repr(typecheck.__name__),
                        "value_type": repr(vtype.__name__),
                    },
                ),
            )
            exc.hint = _(  # type: ignore
                "These may be caused by the wrong type of the value in a json."
            )
            raise exc

        return res

    def update(self, mapping: "dict | AutoFormatDict") -> None:
        """Update the dict with the given mapping.

        Args:
            mapping (dict | AutoFormatDict): The mapping to update.
        """

        if isinstance(mapping, dict):
            mapping = self.from_dict(mapping)

        for key, value in mapping.items():
            self[key] = value

    def merge(self, mapping: "dict | AutoFormatDict") -> None:
        """Merge the dict with the given mapping.

        Args:
            mapping (dict | AutoFormatDict): The mapping to merge.
        """

        if isinstance(mapping, dict):
            mapping = self.from_dict(mapping)

        merge_object(self, mapping)

    def __setitem__(self, key: str, value: Any) -> None:
        """Set the value of the given key.

        Args:
            key (str): The key to set value.
            value (Any): The value to set.
        """

        if isinstance(value, str):
            value = format_str(value)
        super().__setitem__(key, AutoFormatDict.from_dict(value))

    def __getitem__(self, key: str) -> Any:
        """Get the value of the given key.

        Args:
            key (str): The key to get value.

        Returns:
            Any: The value of the given key.
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


def merge_object(obj: AutoFormatDict, src: AutoFormatDict) -> None:
    """Merge the src to the obj.

    Args:
        obj (AutoFormatDict): The object to merge.
        src (AutoFormatDict): The source to merge.
    """

    for key, value in obj.items():
        if isinstance(value, AutoFormatDict):
            merge_object(value, src.get(key, AutoFormatDict()))
        elif isinstance(value, list):
            obj[key].extend(src.get(key, []))  # type: ignore
        else:
            obj[key] = src.get(key, value)  # Overwrite the value.
