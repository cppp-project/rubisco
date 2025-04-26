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

"""Stack implementation."""

from queue import Empty, LifoQueue
from time import time
from typing import Any, Generic, TypeVar

import pytest

__all__ = ["Stack"]


T = TypeVar("T")


class Stack(LifoQueue[T], Generic[T]):
    """A LifoQueue that can get the top value."""

    def top(
        self,
        *,
        block: bool = True,
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


class TestStack:
    """Test the Stack class."""

    def test_stack(self) -> None:
        """Test the Stack class."""
        stack = Stack[int]()
        stack.put(1)
        stack.put(2)
        stack.put(3)
        if str(stack) != "[1, 2, 3>":
            raise AssertionError
        if stack.top() != 3:  # noqa: PLR2004
            raise AssertionError
        if stack.get() != 3:  # noqa: PLR2004
            raise AssertionError
        if stack.get() != 2:  # noqa: PLR2004
            raise AssertionError
        if stack.get() != 1:
            raise AssertionError

    def test_stack_exception(self) -> None:
        """Test the Stack class exception handling."""
        stack = Stack[int]()
        pytest.raises(Empty, stack.get, block=False)
        pytest.raises(Empty, stack.top, block=False)
        stack.put(1)
        with pytest.raises(
            ValueError,
            match="'timeout' must be a non-negative number",
        ):
            stack.get(timeout=-1)
