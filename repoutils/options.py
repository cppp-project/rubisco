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
Get or set program options.
"""

from typing import Any

__all__ = ["get_option", "set_option"]

options: dict[str, Any] = {}


def get_option(name: str, default: Any) -> Any:
    """Get the value of the given option.

    Args:
        name (str): The name of the option.
        default (Any): The default value of the option.

    Returns:
        Any: The value of the option.
    """

    return options.get(name, default)


def set_option(name: str, value: Any):
    """Set the value of the given option.

    Args:
        name (str): The name of the option.
        value (Any): The value of the option.
    """

    options[name] = value
