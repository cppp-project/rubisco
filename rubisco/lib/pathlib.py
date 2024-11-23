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

"""Extended path utilities."""


import os
import pathlib
import sys
from typing import TYPE_CHECKING

__all__ = ["Path"]


class Path(pathlib.Path):
    """Path class with additional methods."""

    def normpath(self) -> "Path":
        """Normalize the path but don't resolve it.

        Returns:
            Path: The normalized path.

        """
        return Path(os.path.normpath(str(self)))  # type: ignore[return-value]


# In Python 3.11, parent's @classmethod will catch children.
if sys.version_info < (3, 12) and not TYPE_CHECKING:
    # "Inject" the extended methods into the built-in pathlib.Path class.
    pathlib.Path.normpath = Path.normpath  # type: ignore[method-required]
    Path = pathlib.Path  # type: ignore[assignment]
