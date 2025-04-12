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

"""Rubisco variable callbacks."""

__all__ = [
    "add_undefined_var_callback",
    "on_undefined_var",
    "undefined_var_callbacks",
]


from collections.abc import Callable

undefined_var_callbacks: list[Callable[[str], None]] = []


def add_undefined_var_callback(callback: Callable[[str], None]) -> None:
    """Add the callback to the list.

    Args:
        callback (Callable[[str], None]): The callback to add.

    """
    undefined_var_callbacks.append(callback)


def on_undefined_var(name: str) -> None:
    """Call the callbacks when a variable is undefined.

    Args:
        name (str): The name of the variable.

    """
    for callback in undefined_var_callbacks:
        callback(name)
