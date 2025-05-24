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

"""Test rubisco.lib.command module."""

import pytest

from rubisco.lib.command import command


class TestCommand:
    """Test rubisco.lib.command module."""

    def test_command_generator(self) -> None:
        """Test command generator."""
        if command(["echo", "Hello, world!"]) != 'echo "Hello, world!"':
            pytest.fail("Incorrect command generated.")
        if command("echo Hello, world!") != "echo Hello, world!":
            pytest.fail("Incorrect command generated.")

    def test_recursive_command_generator(self) -> None:
        """Test recursive command generator."""
        if command(["echo", ["Hello, world!"]]) != 'echo "Hello, world!"':
            pytest.fail("Incorrect command generated.")
        if (
            command(["echo", ["Hello, world!", "Goodbye, world!"]])
            != 'echo "Hello, world!" "Goodbye, world!"'
        ):
            pytest.fail("Incorrect command generated.")
