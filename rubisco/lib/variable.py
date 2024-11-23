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

from __future__ import annotations

import os
import re
import sys
from platform import uname
from queue import Empty, LifoQueue
from time import monotonic as time
from typing import TYPE_CHECKING, Any, Self, overload

from rubisco.config import APP_VERSION, RUBISCO_COMMAND
from rubisco.lib.l10n import _
from rubisco.lib.pathlib import Path

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterable, Iterator
    from types import UnionType

__all__ = [
    "AFTypeError",
    "AutoFormatDict",
    "AutoFormatList",
    "VariableUpdateCallback",
    "add_callback",
    "assert_iter_types",
    "format_str",
    "get_variable",
    "iter_assert",
    "make_pretty",
    "pop_variables",
    "push_variables",
    "undefined_variables",
    "used_variables",
    "variables",
]


class Stack(LifoQueue):
    """A LifoQueue that can get the top value."""

    def top(
        self,
        block: bool = True,  # noqa: FBT001 FBT002
        timeout: int | None = None,
    ) -> Any:  # noqa: ANN401
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
                msg = "'timeout' must be a non-negative number"
                raise ValueError(msg)
            else:
                endtime = time() + timeout
                while not self._qsize():
                    remaining = endtime - time()
                    if remaining <= 0.0:
                        raise Empty
                    self.not_empty.wait(remaining)
            return self.queue[-1]

    def top_nowait(self) -> Any:  # noqa: ANN401
        """Get the top value of the stack without blocking.

        Returns:
            Any: The top value of the stack.

        """
        return self.top(block=False)

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


def push_variables(name: str, value: Any) -> None:  # noqa: ANN401
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


def pop_variables(name: str) -> Any:  # noqa: ANN401
    """Pop the top value of the given variable.

    Args:
        name (str): The name of the variable.

    Returns:
        Any: The top value of the given variable.

    """
    if name in variables:
        res = variables[name].get()
        if variables[name].empty():
            del variables[name]
        return res
    return None


def get_variable(name: str) -> Any:  # noqa: ANN401
    """Get the value of the given variable.

    Args:
        name (str): The name of the variable.

    Returns:
        Any: The value of the given variable.

    Raises:
        KeyError: If the variable is not found.

    """
    if name in variables:
        if name not in used_variables:
            old = used_variables.copy()
            used_variables.add(name)
            for callback in callbacks:
                callback.on_used_variables_update(old)
        return variables[name].top()
    if name not in undefined_variables:
        old = undefined_variables.copy()
        undefined_variables.add(name)
        for callback in callbacks:
            callback.on_undefined_variables_update(old)
    raise KeyError(repr(name))


def make_pretty(string: str | Any, empty: str = "") -> str:  # noqa: ANN401
    """Make the string pretty.

    Args:
        string (str | Any): The string to get representation.
        empty (str): The string to return if the input is empty.

    Returns:
        str: Result string.

    """
    string = str(string)

    if not string:
        return empty
    if string.endswith("\\"):
        string += "\\"

    return string


def assert_iter_types(
    iterable: Iterable,
    objtype: type | UnionType,
    exc: Exception,
) -> None:
    """Assert the types of the elements in the iterable.

    Args:
        iterable (Iterable): The iterable to assert.
        objtype (type | UnionType): The type to assert.
        exc (Exception): The exception to raise.

    Raises:
        Exception: If the type of the element is not the same as the given.

    """
    if objtype in [dict, AutoFormatDict]:
        objtype = dict | AutoFormatDict

    for obj in iterable:
        if not isinstance(obj, objtype):
            raise exc


def iter_assert(
    iterable: Iterable[Any],
    checker: Callable[[Any], bool],
    exc: Exception | Callable[[Any], Exception],
) -> None:
    """Iterate the iterable and assert the elements.

    Args:
        iterable (Iterable[Any]): The iterable to iterate.
        checker (Callable[[Any], bool]): Element checker.
            The argument is the element in the iterable.
        exc (Exception | Callable[Any]): The exception to raise or the
            `on_error` callback. The argument is the element in the iterable.
            Returns the exception to raise.

    Raises:
        Exception: If the element does not pass the checker

    """
    if isinstance(exc, Exception):
        exc_ = exc

        def _exc(
            e: Any,  # noqa: ARG001 ANN401 # pylint: disable=unused-argument
        ) -> Exception:
            return exc_
        exc = _exc

    for obj in iterable:
        if not checker(obj):
            raise exc(obj)


uname_result = uname()

# Built-in variables.
push_variables("home", str(Path.home().absolute()))
push_variables("cwd", str(Path.cwd().absolute()))
push_variables("nproc", os.cpu_count())
push_variables("rubisco.version", str(APP_VERSION))
push_variables("rubisco.command", str(RUBISCO_COMMAND))
push_variables("rubisco.python_version", sys.version)
push_variables("rubisco.python_impl", sys.implementation.name)
push_variables("host.os", os.name)
push_variables("host.system", uname_result.system)
push_variables("host.node", uname_result.node)
push_variables("host.release", uname_result.release)
push_variables("host.version", uname_result.version)
push_variables("host.machine", uname_result.machine)
push_variables("host.processor", uname_result.processor)


# Unused now. May be used in extensions.
class VariableUpdateCallback:
    """Variable update callback.

    The callback called when the `used_variables` and `undefined_variables`
    are updated.
    """

    def on_used_variables_update(self, old: set[str]) -> None:
        """When the `used_variables` are updated.

        Args:
            old (set[str]): The old `used_variables`.

        """

    def on_undefined_variables_update(self, old: set[str]) -> None:
        """When the `undefined_variables` are updated.

        Args:
            old (set[str]): The old `undefined_variables`.

        """


# The variables that are used.
used_variables = set()

# The variables that are used but not defined.
undefined_variables = set()

callbacks: list[VariableUpdateCallback] = []


def add_callback(callback: VariableUpdateCallback) -> None:
    """Add the callback to the list.

    Args:
        callback (VariableUpdateCallback): The callback to add.

    """
    callbacks.append(callback)


# Toooo complex, need review.
def format_str(  # noqa: C901
    string: str | Any,  # noqa: ANN401
    fmt: dict[str, Stack | str] | None = None,
) -> str | Any:  # noqa: ANN401
    """Format the string with variables.

    Args:
        string (str | Any): The string to format.
        fmt (dict[str, Stack | str] | None): The format dictionary.
            Defaults to None.

    Returns:
        str | Any: The formatted string. If the input is not a string,
            return itself.

    """
    if not isinstance(string, str):
        return string

    if fmt is None:
        fmt = {}

    fmt = variables | fmt

    # If string only contains one variable, return the value directly.
    if string.startswith("${{") and string.endswith("}}"):
        key = string[3:-2].strip()
        res = fmt.get(key, string)
        if isinstance(res, Stack):
            res = res.top()

    matches = re.findall(r"\$\{\{ *[\d|_|\-|a-z|A-Z|.]+ *\}\}", string)
    # If string only contains one variable, return the value directly.
    if len(matches) == 1 and string == matches[0]:
        key = string[3:-2].strip()
        res = fmt.get(key, string)
        if isinstance(res, Stack):
            res = res.top()
        return res

    for match in matches:
        key = match[3:-2].strip()
        if key not in used_variables:
            old = used_variables.copy()
            used_variables.add(key)
            for callback in callbacks:
                callback.on_used_variables_update(used_variables)
                fmt = variables | fmt
        res = fmt.get(key, match)
        if key not in fmt:
            old = undefined_variables.copy()
            undefined_variables.add(key)
            for callback in callbacks:
                callback.on_undefined_variables_update(old)
        if isinstance(res, Stack):
            res = res.top()
        string = string.replace(match, str(res))

    return string


def _to_autotype(obj: Any) -> Any:  # noqa: ANN401
    """Convert the list or dict object to AutoFormatList or AutoFormatDict.

    If not list or dict, return itself.
    """
    if isinstance(obj, dict) and not isinstance(obj, AutoFormatDict):
        return AutoFormatDict(obj)
    if isinstance(obj, list) and not isinstance(obj, AutoFormatList):
        return AutoFormatList(obj)

    return obj


class AutoFormatList(list):
    """A list that can format value automatically with variables.

    We will replace all the elements which are lists or dicts to
    AutoFormatList or AutoFormatDict recursively.
    The elements will be formatted when we get them.
    Python's built-in list and dict will NEVER appear here.
    """

    def __init__(self, iterable: Iterable = ()) -> None:
        """Initialize the AutoFormatList.

        Args:
            iterable (Iterable, optional): The iterable to initialize the list.
                Defaults to ().

        """
        super().__init__([_to_autotype(item) for item in iterable])

    def append(self, value: Any) -> None:  # noqa: ANN401
        """Append the value to the list.

        Args:
            value (Any): The value to append.

        """
        super().append(_to_autotype(value))

    raw_count = list.count

    def count(self, value: Any) -> int:  # noqa: ANN401
        """Count the value in the list.

        Args:
            value (Any): The value to count.

        Returns:
            int: The count of the value.

        """
        counts = 0
        for item in self:
            if format_str(item) == format_str(value):
                counts += 1

        return counts

    raw_extend = list.extend

    def extend(self, iterable: Iterable) -> None:
        """Extend the list with the given iterable.

        Args:
            iterable (Iterable): The iterable to extend.

        """
        for value in iterable:
            self.append(_to_autotype(value))

    raw_index = list.index

    def index(
        self,
        value: Any,  # noqa: ANN401
        start: int = 0,
        stop: int = sys.maxsize,
    ) -> int:
        """Get the index of the value in the list.

        Args:
            value (Any): The value to get index.
            start (int, optional): The start index. Defaults to 0.
            stop (int, optional): The stop index. Defaults to sys.maxsize.

        Returns:
            int: The index of the value.

        """
        for index, item in enumerate(self[start:stop]):
            if format_str(item) == format_str(value):
                return index

        raise ValueError(repr(value))

    raw_insert = list.insert

    def insert(self, index: int, obj: Any) -> None:  # noqa: ANN401
        """Insert the object to the given index.

        Args:
            index (int): The index to insert object.
            obj (Any): The object to insert.

        """
        super().insert(index, _to_autotype(obj))

    raw_remove = list.remove

    def pop(self, index: int = -1) -> Any:  # noqa: ANN401
        """Pop the value of the given index.

        Args:
            index (int, optional): The index to pop value. Defaults to -1.

        Returns:
            Any: The value of the given index.

        """
        return format_str(super().pop(index))

    def __setitem__(self, index: int, value: Any) -> None:  # noqa: ANN401
        """Set the value of the given index.

        Args:
            index (int): The index to set value.
            value (Any): The value to set.

        """
        super().__setitem__(index, _to_autotype(value))

    raw_getitem = list.__getitem__

    @overload
    def __getitem__(self, index: int) -> Any:  # noqa: ANN401
        ...

    @overload
    def __getitem__(self, index: slice) -> Self: ...

    def __getitem__(self, index: int | slice) -> Any:
        """Get the value of the given index.

        Args:
            index (int | slice): The index to get value.

        Returns:
            Any: The value of the given index.

        """
        if isinstance(index, int):
            return format_str(super().__getitem__(index))
        return AutoFormatList(super().__getitem__(index))

    raw_iter = list.__iter__

    def __iter__(
        self,
    ) -> Generator[Any, None, None]:  # type: ignore[signature-mismatch]
        """Get the iterator of the list."""
        for item in super().__iter__():
            yield format_str(item)

    raw_repr = list.__repr__

    def __repr__(self) -> str:
        """Get the string representation of the list.

        Returns:
            str: The string representation of the list.

        """
        return f"[{', '.join([repr(item) for item in self])}]"


class AFTypeError(TypeError):
    """AutoFormatDict valtype error."""


class AutoFormatDict(dict):
    """A dictionary that can format value automatically with variables.

    We will replace all the elements which are lists or dicts to
    AutoFormatList or AutoFormatDict recursively.
    The elements will be formatted when we get them.
    Python's built-in list and dict will NEVER appear here.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        """Initialize the AutoFormatDict.

        Args:
            *args: The arguments to initialize the dict.
            **kwargs: The keyword arguments to initialize the dict.

        """
        super().__init__(*args, **kwargs)
        for key, value in self.items():
            # Replace the value with AutoFormatList or AutoFormatDict.
            self[key] = value

    raw_get = dict.get

    @overload
    def get(self, key: str) -> Any:  # noqa: ANN401
        ...

    @overload
    def get(self, key: str, valtype: type | UnionType) -> Any:  # noqa: ANN401
        ...

    @overload
    def get(self, key: str, default: Any) -> Any:  # noqa: ANN401
        ...

    @overload
    def get(
        self,
        key: str,
        default: Any,  # noqa: ANN401
        valtype: type | UnionType,
    ) -> Any:  # noqa: ANN401
        ...

    def get(self, key: str, *args: Any, **kwargs: Any) -> Any:
        """Get the value of the given key.

        Args:
            key (str): The key to get value.
            *args: The arguments to get value.
            **kwargs: The keyword arguments to get value.

        Raises:
            KeyError: If the key is not found.
            AFTypeError: If the value is not the same as the given type.

        Returns:
            Any: The value of the given key.

        """
        valtype = kwargs.pop("valtype", object)
        if valtype == AutoFormatDict:
            valtype = dict
        elif valtype == AutoFormatList:
            valtype = list
        if len(args) == 1:
            res = format_str(self.raw_get(format_str(key), args[0]))
        elif "default" in kwargs:
            res = format_str(
                self.raw_get(format_str(key), kwargs["default"]),
            )
        else:
            key = format_str(key)
            if key not in self:
                raise KeyError(repr(key))
            res = format_str(super().get(key))
        if not isinstance(res, valtype):
            if hasattr(valtype, "__name__"):
                valtype_name = valtype.__name__
            else:
                valtype_name = f"'{valtype}'"
            raise AFTypeError(
                format_str(
                    _(
                        "The value of key ${{key}} needs to be ${{type}}"
                        " instead of ${{value_type}}.",
                    ),
                    fmt={
                        "key": repr(key),
                        "type": valtype_name,
                        "value_type": repr(type(res).__name__),
                    },
                ),
            )
        return res

    raw_keys = dict.keys

    def keys(
        self,
    ) -> Generator[str, None, None]:  # type: ignore[signature-mismatch]
        """Get the keys of the dict."""
        for key in super().keys():  # noqa: SIM118
            yield format_str(key)

    raw_values = dict.values

    def values(
        self,
    ) -> Generator[Any, None, None]:  # type: ignore[signature-mismatch]
        """Get the values of the dict."""
        for value in super().values():
            yield format_str(value)

    raw_items = dict.items

    def items(
        self,
    ) -> list[tuple[str, Any]]:  # type: ignore[signature-mismatch]
        """Get the items of the dict."""
        return list(zip(list(self.keys()), list(self.values()), strict=False))

    def update(self, src: dict | AutoFormatDict | None = None) -> None:
        """Update the dict with the given mapping.

        Args:
            src (dict | AutoFormatDict): The mapping to update.

        """
        if src is None:
            return

        if isinstance(src, dict) and not isinstance(src, AutoFormatDict):
            src = AutoFormatDict(src)

        for key, value in src.items():
            self[key] = value

    raw_pop = dict.pop

    @overload
    def pop(self, key: str) -> Any: ...  # noqa: ANN401

    @overload
    def pop(self, key: str, default: Any) -> Any:  # noqa: ANN401
        ...

    def pop(self, key: str, *args: Any, **kwargs: Any) -> Any:
        """Pop the value of the given key.

        Args:
            key (str): The key to pop value.
            *args: The arguments to pop value.
            **kwargs: The keyword arguments to pop value.

        Returns:
            Any: The value of the given key.

        """
        if len(args) == 1:
            res = format_str(super().pop(format_str(key), args[0]))
        elif "default" in kwargs:
            res = format_str(
                super().pop(format_str(key), kwargs["default"]),
            )
        else:
            res = format_str(super().pop(format_str(key)))
        return res

    def copy(self) -> AutoFormatDict:
        """Get a copy of the dict.

        Returns:
            AutoFormatDict: The copy of the dict.

        """
        return AutoFormatDict(self)

    def popitem(self) -> tuple[str, Any]:
        """Pop the item of the dict.

        Returns:
            tuple[str, Any]: The item of the dict.

        """
        key, value = super().popitem()
        return format_str(key), format_str(value)

    def merge(self, mapping: dict | Self) -> None:
        """Merge the dict with the given mapping.

        Merge is a recursive operation. It can update all the values
        in the dict, including the nested dicts and lists.

        Args:
            mapping (dict | AutoFormatDict): The mapping to merge.

        """
        mapping = _to_autotype(mapping)

        for key, value in mapping.items():
            if key not in self or not isinstance(
                value,
                AutoFormatDict | AutoFormatList,
            ):
                self[key] = value
            elif isinstance(value, AutoFormatDict):
                if not isinstance(self[key], AutoFormatDict):
                    self[key] = AutoFormatDict()
                self[key].merge(value)
            else:  # AutoFormatList
                if not isinstance(self[key], AutoFormatList):
                    self[key] = AutoFormatList()
                self[key].extend(value)

    def __setitem__(self, key: str, value: Any) -> None:  # noqa: ANN401
        """Set the value of the given key.

        Args:
            key (str): The key to set value.
            value (Any): The value to set.

        """
        super().__setitem__(key, _to_autotype(value))

    def __getitem__(self, key: str) -> Any:  # noqa: ANN401
        """Get the value of the given key.

        Args:
            key (str): The key to get value.

        Returns:
            Any: The value of the given key.

        """
        return format_str(self.get(format_str(key)))

    def __iter__(self) -> Iterator[str]:
        """Get the keys iterator of the dict."""
        return self.keys()

    def __repr__(self) -> str:
        """Get the string representation of the dict.

        Returns:
            str: The string representation of the dict.

        """
        kvs = [f"{key!r}: {value!r}" for key, value in self.items()]

        return f"{{{', '.join(kvs)}}}"

    def __eq__(self, other: object) -> bool:
        """Check if the dict is equal to the other.

        Args:
            other (object): The other object to compare.

        Returns:
            bool: If the dict is equal to the other.

        """
        if not isinstance(other, dict):
            return False

        for key, value in self.items():
            if key not in other or other[key] != value:
                return False

        return True

    def __ne__(self, other: object) -> bool:
        """Check if the dict is not equal to the other.

        Args:
            other (object): The other object to compare.

        Returns:
            bool: If the dict is not equal to the other.

        """
        return not self.__eq__(other)

    @classmethod
    def fromkeys(
        cls,
        keys: Iterable,
        value: Any = None,  # noqa: ANN401
    ) -> Self:
        """Create a new dict with the given keys and value.

        Args:
            keys (Iterable): The keys to create the dict.
            value (Any, optional): The value to create the dict. Defaults to
                None.

        Returns:
            AutoFormatDict: The new dict.

        """
        return cls({key: value for key in keys})


def merge_object(obj: AutoFormatDict, src: dict | AutoFormatDict) -> None:
    """Merge the src to the obj.

    Args:
        obj (AutoFormatDict): The object to merge.
        src (dict | AutoFormatDict): The source to merge.

    """
    for key, value in obj.items():
        if isinstance(value, AutoFormatDict):
            merge_object(value, src.get(key, {}))
        elif isinstance(value, list):
            obj[key].extend(src.get(key, []))  # type: ignore[union-attr]
        else:
            obj[key] = src.get(key, value)  # Overwrite the value.
    for key, value in src.items():
        if key not in obj:
            obj[key] = value


if __name__ == "__main__":
    import pytest
    import rich

    # Test: Variables.
    rich.print(variables)

    # Test: Merge the AutoFormatDict.
    afd = AutoFormatDict()
    afd["test"] = "test"
    afd.merge({"test": "merged", "non": "ok"})
    rich.print(afd)
    assert afd == {"test": "merged", "non": "ok"}  # noqa: S101

    # Test: Getting the value of the key.
    afd = AutoFormatDict({"test": "testval"})
    assert afd.get("test") == "testval"  # noqa: S101
    assert afd.get("non", "ok") == "ok"  # noqa: S101
    assert afd.get("test", valtype=str) == "testval"  # noqa: S101
    assert afd.get("non", 0, valtype=int) == 0  # noqa: S101
    assert afd.get("non", "ok", valtype=str) == "ok"  # noqa: S101
    pytest.raises(KeyError, lambda: afd.get("non"))

    # Test: Args and kwargs of get().
    assert afd.get("test", valtype=str) == "testval"  # noqa: S101
    pytest.raises(AFTypeError, lambda: afd.get("test", valtype=int))
    assert afd.get("non", "ok", valtype=str) == "ok"  # noqa: S101
    pytest.raises(KeyError, lambda: afd.get("non", valtype=int))
    assert afd.get("non", "ok") == "ok"  # noqa: S101
    assert afd.get("non", "ok", valtype=str) == "ok"  # noqa: S101

    push_variables("test", "test")
    assert get_variable("test") == "test"  # noqa: S101
    assert AutoFormatDict(  # noqa: S101
        {"${{test}}": "${{test}}"},
    ) == {"test": "test"}
    assert pop_variables("test") == "test"  # noqa: S101
