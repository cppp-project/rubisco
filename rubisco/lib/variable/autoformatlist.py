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

"""AutoFormatList implementation."""

import sys
from collections.abc import Generator, Iterable
from typing import Any, Generic, Self, SupportsIndex, TypeVar, cast

from rubisco.lib.variable.format import format_str
from rubisco.lib.variable.to_autotype import to_autotype

T = TypeVar("T")


class AutoFormatList(list[T], Generic[T]):
    """A list that can format value automatically with variables.

    We will replace all the elements which are lists or dicts to
    AutoFormatList or AutoFormatDict recursively.
    The elements will be formatted when we get them.
    Python's built-in list and dict will NEVER appear here.
    """

    def __init__(self, iterable: Iterable[T] = ()) -> None:
        """Initialize the AutoFormatList.

        Args:
            iterable (Iterable[T], optional): The iterable to initialize the
                list. Defaults to ().

        """
        super().__init__([to_autotype()(item) for item in iterable])

    def append(self, value: T) -> None:
        """Append the value to the list.

        Args:
            value (T): The value to append.

        """
        super().append(to_autotype()(value))

    orig_count = list[T].count

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

    orig_extend = list[T].extend

    def extend(self, iterable: Iterable[T]) -> None:
        """Extend the list with the given iterable.

        Args:
            iterable (Iterable[T]): The iterable to extend.

        """
        for value in iterable:
            self.append(to_autotype()(value))

    orig_index = list[T].index

    def index(
        self,
        value: T,
        start: SupportsIndex = 0,
        stop: SupportsIndex = sys.maxsize,
    ) -> int:
        """Get the index of the value in the list.

        Args:
            value (T): The value to get index.
            start (SupportsIndex, optional): The start index. Defaults to 0.
            stop (SupportsIndex, optional): The stop index.
                Defaults to sys.maxsize.

        Returns:
            int: The index of the value.

        Raises:
            ValueError: If the value is not in the list.

        """
        for index, item in enumerate(cast("list[T]", self[start:stop])):
            if format_str(item) == format_str(value):
                return index

        raise ValueError(value)

    orig_insert = list[T].insert

    def insert(self, index: SupportsIndex, obj: Any) -> None:  # noqa: ANN401
        """Insert the object to the given index.

        Args:
            index (SupportsIndex): The index to insert object.
            obj (Any): The object to insert.

        """
        super().insert(index, to_autotype()(obj))

    orig_remove = list[T].remove

    def pop(self, index: SupportsIndex = -1) -> Any:  # noqa: ANN401
        """Pop the value of the given index.

        Args:
            index (SupportsIndex, optional): The index to pop value.
                Defaults to -1.

        Returns:
            Any: The value of the given index.

        """
        return format_str(super().pop(index))

    def __setitem__(
        self,
        index: SupportsIndex | slice,
        value: T | Iterable[T],
    ) -> None:
        """Set the value of the given index.

        Args:
            index (SupportsIndex | slice): The index to set value.
            value (T | Iterable[T]): The value to set.

        """
        if isinstance(index, slice):
            value = [to_autotype()(item) for item in cast("Iterable[T]", value)]
            for i in range(index.start, index.stop, index.step):
                self[i] = value[i]
            return
        super().__setitem__(index, to_autotype()(value))

    orig_getitem = list[T].__getitem__

    def __getitem__(  # type: ignore[valid-type]
        self,
        index: int | slice,
    ) -> "T | AutoFormatList[T]":
        """Get the value of the given index.

        Args:
            index (int | slice): The index to get value.

        Returns:
            T | AutoFormatList[T]: The value of the given index.

        """
        if isinstance(index, int):
            return format_str(super().__getitem__(index))
        return AutoFormatList(super().__getitem__(index))

    def __contains__(self, value: Any) -> bool:  # noqa: ANN401
        """Check if the value is in the list.

        Args:
            value (Any): The value to check.

        Returns:
            bool: True if the value is in the list, False otherwise.

        """
        return any(format_str(item) == format_str(value) for item in self)

    def __add__(self, other: Iterable[Any]) -> "AutoFormatList[Any]":
        """Add the other iterable to the list.

        Args:
            other (Iterable[Any]): The iterable to add.

        Returns:
            AutoFormatList[Any]: The new list.

        """
        res = AutoFormatList(self)
        res.extend(other)
        return res

    def __iadd__(self, other: Iterable[Any]) -> Self:
        """Add the other iterable to the list.

        Args:
            other (Iterable[Any]): The iterable to add.

        Returns:
            Self: The new list.

        """
        self.extend(other)
        return self

    def __eq__(
        self,
        other: object,
    ) -> bool:
        """Check if the list is equal to the other iterable.

        Args:
            other (object): The iterable
                to check.

        Returns:
            bool: True if the list is equal to the other iterable, False
                otherwise.

        """
        if not isinstance(other, list | AutoFormatList):
            return False

        if len(self) != len(cast("list[Any]", other)):
            return False

        for item1, item2 in zip(self, cast("list[Any]", other), strict=False):
            if format_str(item1) != format_str(item2):
                return False
        return True

    orig_iter = list[T].__iter__

    def __iter__(
        self,
    ) -> Generator[Any, None, None]:  # type: ignore[signature-mismatch]
        """Get the iterator of the list."""
        for item in super().__iter__():
            yield format_str(item)

    orig_repr = list[T].__repr__

    def __repr__(self) -> str:
        """Get the string representation of the list.

        Returns:
            str: The string representation of the list.

        """
        return f"[{', '.join([repr(item) for item in self])}]"
