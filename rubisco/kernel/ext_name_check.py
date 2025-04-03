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

"""Check if the extension name is valid.

Don't implement this module in `rubisco/shared/extension.py` because
it will cause circular import.
"""

import re

from rubisco.config import VALID_EXTENSION_NAME

__all__ = ["is_valid_extension_name"]

INVALID_EXT_NAMES = ["rubisco"]  # Avoid logger's name conflict.


def is_valid_extension_name(name: str) -> bool:
    """Check if the extension name is valid.

    Args:
        name (str): The extension name.

    Returns:
        bool: True if the extension name is valid, otherwise False.

    """
    return name not in INVALID_EXT_NAMES and bool(
        re.match(
            VALID_EXTENSION_NAME,
            name,
        ),
    )
