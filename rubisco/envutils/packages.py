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

"""Package management utils for environment."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rubisco.lib.version import Version


class ExtensionPackage:  # pylint: disable=too-few-public-methods
    """A package."""

    name: str
    version: Version
    dependencies: list[list[str]]

    def __init__(
        self,
        name: str,
        version: Version,
        dependencies: list[list[str]],
    ) -> None:
        """Initialize the package.

        Args:
            name (str): The package name.
            version (Version): The package version.
            dependencies (list[list[str]]): The package dependencies.

        """
        self.name = name
        self.version = version
        self.dependencies = dependencies


if __name__ == "__main__":
    pass
