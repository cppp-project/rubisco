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
Stack type definition.
"""

from typing import Any, Iterable, Iterator, overload
import threading
import asyncio
import copy

__all__ = ["Stack"]


class Stack:
    """Stack type."""

    __stack: list[Any]
    __lock: threading.Lock

    @overload
    def __init__(self):
        """Initialize the stack."""

    @overload
    def __init__(self, init: "Stack"):
        """Initialize the stack."""

    @overload
    def __init__(self, init: Iterable[Any]):
        """Initialize the stack."""

    def __init__(self, *args):
        """Initialize the stack."""

        self.__lock = threading.Lock()
        if len(args) == 0:
            self.__stack = []
        elif len(args) == 1:
            self.__stack = list(args[0]).copy()
        else:
            raise TypeError(
                f"Stack() takes 0 or 1 positional arguments but {len(args)} were given."  # noqa: E501 # pylint: disable=line-too-long
            )

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

        return f"[{', '.join([repr(item) for item in self.__stack])}>"

    def __getitem__(self, index: int) -> Any:
        """Get the item at the given index.

        Args:
            index (int): The index of the item.

        Returns:
            The item at the given index.

        Warning:
            Standard stack do not support negative index.
        """

        return self.__stack[index]

    def __setitem__(self, index: int, item: Any) -> None:
        """Set the item at the given index.

        Args:
            index (int): The index of the item.
            item (Any): The item to be set.

        Warning:
            Standard stack do not support negative index.
        """

        self.__stack[index] = item

    def __delitem__(self, index: int) -> None:
        """Delete the item at the given index.

        Args:
            index (int): The index of the item.

        Warning:
            Standard stack do not support delete item at negative index.
        """

        del self.__stack[index]

    def __len__(self) -> int:
        """Get the size of the stack.

        Returns:
            The size of the stack.
        """

        return self.size()

    def __contains__(self, item: Any) -> bool:
        """Check if the stack contains the given item.

        Args:
            item (Any): The item to be checked.

        Returns:
            True if the stack contains the given item, otherwise False.
        """

        return item in self.__stack

    def __iter__(self) -> Iterator[Any]:
        """Get the iterator of the stack.

        Returns:
            The iterator of the stack.
        """

        return iter(self.__stack)

    def __add__(self, other: "Stack") -> "Stack":
        """Concatenate two stacks.

        Args:
            other (Stack): The other stack.

        Returns:
            Stack: The concatenated stack.

        """

        return Stack(self.__stack + list(other))

    def __list__(self) -> list[Any]:
        """Get the list of the stack.

        Returns:
            list[Any]: The list of the stack.
        """

        return self.__stack

    def __copy__(self) -> "Stack":
        """Copy the stack.

        Returns:
            Stack: The copied stack.
        """

        return Stack(self)

    def __bool__(self) -> bool:
        """Check if the stack is empty.

        Returns:
            True if the stack is empty, otherwise False.
        """

        return not self.empty()

    def __eq__(self, other: "Stack") -> bool:
        """Check if two stacks are equal.

        Args:
            other (Stack): The other stack.

        Returns:
            True if two stacks are equal, otherwise False.
        """

        return self.__stack == list(other)

    def __ne__(self, other: "Stack") -> bool:
        """Check if two stacks are not equal.

        Args:
            other (Stack): The other stack.

        Returns:
            True if two stacks are not equal, otherwise False.
        """

        return self.__stack != list(other)

    def __lt__(self, other: "Stack") -> bool:
        """Check if the stack is less than the other stack.

        Args:
            other (Stack): The other stack.

        Returns:
            True if the stack is less than the other stack, otherwise False.
        """

        return self.__stack < list(other)

    def __le__(self, other: "Stack") -> bool:
        """Check if the stack is less than or equal to the other stack.

        Args:
            other (Stack): The other stack.

        Returns:
            True if the stack is less than or equal to the other stack,
                otherwise False.
        """

        return self.__stack <= list(other)

    def __gt__(self, other: "Stack") -> bool:
        """Check if the stack is greater than the other stack.

        Args:
            other (Stack): The other stack.

        Returns:
            True if the stack is greater than the other stack, otherwise False.
        """

        return self.__stack > list(other)

    def __ge__(self, other: "Stack") -> bool:
        """Check if the stack is greater than or equal to the other stack.

        Args:
            other (Stack): The other stack.

        Returns:
            True if the stack is greater than or equal to the other stack,
                otherwise False.
        """

        return self.__stack >= list(other)

    def push(self, item: Any) -> "Stack":
        """Push an new item to the stack.

        Args:
            item (Any): The item to be pushed.

        Returns:
            Stack: The stack itself.
        """

        with self.__lock:
            self.__stack.append(item)
        return self

    def push_all(self, items: Iterable[Any]) -> "Stack":
        """Push a list of items to the stack.

        Args:
            items (Iterable[Any]): The items to be pushed.

        Returns:
            Stack: The stack itself.
        """

        with self.__lock:
            self.__stack.extend(items)
        return self

    async def push_async(self, item: Any):
        """Push an new item to the stack asynchronously.

        Args:
            item (Any): The item to be pushed.
        """

        await asyncio.get_event_loop().run_in_executor(None, self.push, item)

    async def push_all_async(self, items: Iterable[Any]):
        """Push a list of items to the stack asynchronously.

        Args:
            items (Iterable[Any]): The items to be pushed.
        """

        await asyncio.get_event_loop().run_in_executor(  # noqa: E501
            None, self.push_all, items
        )

    def pop(self):
        """Pop the top item of the stack.

        Returns:
            The top item of the stack.
        """

        with self.__lock:
            if len(self) == 0:
                raise IndexError("Pop from empty stack.")
            return self.__stack.pop()

    def pop_all(self) -> list[Any]:
        """Pop all items of the stack.

        Returns:
            list[Any]: The items of the stack.
        """

        with self.__lock:
            items = self.__stack.copy()
            self.__stack.clear()
            return items

    async def pop_async(self):
        """Pop the top item of the stack asynchronously.

        Returns:
            The top item of the stack.
        """

        return await asyncio.get_event_loop().run_in_executor(None, self.pop)

    async def pop_all_async(self) -> list[Any]:
        """Pop all items of the stack asynchronously.

        Returns:
            list[Any]: The items of the stack.
        """

        return await asyncio.get_event_loop().run_in_executor(  # noqa: E501
            None, self.pop_all
        )

    def top(self) -> Any:
        """Get the top item of the stack.

        Returns:
            The top item of the stack.
        """

        if len(self.__stack) == 0:
            return None
        return self.__stack[-1]

    def size(self) -> int:
        """Get the size of the stack.

        Returns:
            The size of the stack.
        """

        return len(self.__stack)

    def empty(self) -> bool:
        """Check if the stack is empty.

        Returns:
            True if the stack is empty, otherwise False.
        """

        return self.size() == 0

    def clear(self) -> "Stack":
        """Clear the stack.

        Returns:
            Stack: The stack itself.
        """

        with self.__lock:
            self.__stack.clear()
        return self

    def clear_async(self) -> "Stack":
        """Clear the stack asynchronously."""

        return asyncio.get_event_loop().run_in_executor(None, self.clear)

    def copy(self) -> "Stack":
        """Copy the stack.

        Returns:
            Stack: The copied stack.
        """

        return copy.copy(self)

    def copy_async(self) -> "Stack":
        """Copy the stack asynchronously.

        Returns:
            Stack: The copied stack.
        """

        return asyncio.get_event_loop().run_in_executor(None, self.copy)


if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    stack = Stack()
    print(f"This is an empty stack: {repr(stack)}")
    stack.push(1)
    stack.push(2)
    stack.push("STR")
    print(f"This is a stack with 3 items: {repr(stack)}")
    print(f"Pop the top item: {repr(stack.pop())}")
    print(f"This is a stack with 2 items: {repr(stack)}")
    print(f"Pop all items: {repr(stack.pop_all())}")
    print(f"This is an empty stack: {repr(stack)}")
    stack.push_all([4, 5, 6])
    print(f"Now the stack has 3 items: {repr(stack)}")
    print(f"The size of the stack is {len(stack)}")

    del stack[0]
    print(f"Delete the first item: {repr(stack)}")

    stack_copy = stack.copy()
    print(
        f"This is the copy of the stack: {repr(stack_copy)}, {id(stack)} => {id(stack_copy)}"  # noqa: E501 # pylint: disable=line-too-long
    )
    print(f"{stack_copy} == {stack}: {stack_copy == stack}")

    print("Now check the stack in async mode.")

    async def _check_async():
        print(f"Push an item to the stack asynchronously: {repr(stack)}")
        await stack.push_async(7)
        print(
            f"Push a list of items to the stack asynchronously: {repr(stack)}"
        )  # noqa: E501 # pylint: disable=line-too-long
        await stack.push_all_async([8, 9, 10])
        print(f"Pop the top item of the stack asynchronously: {repr(stack)}")
        await stack.pop_async()
        print(f"Pop all items of the stack asynchronously: {repr(stack)}")
        await stack.pop_all_async()
        print(f"Get the top item of the stack asynchronously: {repr(stack)}")
        print(f"Top item: {stack.top()}")
        print(f"Stack size: {stack.size()}")
        await stack.clear_async()
        print(f"Cleared stack: {repr(stack)}")
        await stack.push_all_async([4, 5, 6])
        print(f"Now the stack has 3 items: {repr(stack)}")
        stack_copy2 = await stack.copy_async()
        print(
            f"This is the copy of the stack: {repr(stack_copy2)}, {id(stack)} => {id(stack_copy2)}"  # noqa: E501 # pylint: disable=line-too-long
        )

    asyncio.run(_check_async())
    print("Done.")
