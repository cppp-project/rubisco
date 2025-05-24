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

"""Test rubisco.lib.stack module."""

from queue import Empty

import pytest

from rubisco.lib.stack import Stack


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
