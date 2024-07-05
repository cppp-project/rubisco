# -*- coding: utf-8 -*-
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

"""
Version numbering analysis and comparison module.
"""

import re
from typing import overload

__all__ = ["Version"]


class Version:
    """
    Version analyzer.
    """

    major: int
    minor: int
    patch: int
    pre: str
    build: str

    @overload
    def __init__(self, version: str) -> None:
        """Analyze the version string.

        Args:
            version (str): The version string.
        """

    @overload
    def __init__(self, version: "Version") -> None:
        """Copy a version info.

        Args:
            version (Version): The version.
        """

    @overload
    def __init__(self, version: tuple) -> None:
        """Analyze the version tuple.

        Args:
            version (tuple): The version tuple.
        """

    def __init__(self, version: "str | Version | tuple") -> None:
        self.major = 0
        self.minor = 0
        self.patch = 0
        self.pre = ""
        self.build = ""

        if isinstance(version, str):
            self._analyze(version)
        elif isinstance(version, Version):
            self.major = version.major
            self.minor = version.minor
            self.patch = version.patch
            self.pre = version.pre
            self.build = version.build
        elif isinstance(version, tuple):
            self.major = int(version[0])
            self.minor = int(version[1])
            self.patch = int(version[2])
            if len(version) > 3:
                self.pre = str(version[3])
            if len(version) > 4:
                self.build = str(version[4])
        else:
            raise ValueError("Invalid version type.")

    def _analyze(self, version: str) -> None:
        """Analyze the version string.

        Args:
            version (str): The version string.
        """

        match = re.match(
            r"(\d+)\.(\d+)\.(\d+)(?:-(\w+))?(?:\+(\w+))?",
            version,
        )
        if match:
            self.major = int(match.group(1))
            self.minor = int(match.group(2))
            self.patch = int(match.group(3))
            self.pre = match.group(4) or ""
            self.build = match.group(5) or ""

    def __str__(self) -> str:
        """Get the version string.

        Returns:
            str: The version string.
        """

        verstr = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre:
            verstr += f"-{self.pre}"
        if self.build:
            verstr += f"+{self.build}"
        return verstr

    def __repr__(self) -> str:
        """Get the instance representation.

        Returns:
            str: The version string.
        """

        return f"Version({str(self)})"

    def __eq__(self, other: "Version") -> bool:
        """Compare two versions for equality.

        Args:
            other (Version): The other version.

        Returns:
            bool: True if equal, False otherwise.
        """

        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
            and self.pre == other.pre
            and self.build == other.build
        )

    def __ne__(self, other) -> bool:
        """Compare two versions for inequality.

        Args:
            other (Version): The other version.

        Returns:
            bool: True if not equal, False otherwise.
        """

        return not self.__eq__(other)

    def __lt__(  # pylint: disable=too-many-return-statements
        self,
        other: "Version",
    ) -> bool:
        """Compare two versions for less than.

        Args:
            other (Version): The other version.

        Returns:
            bool: True if less than, False otherwise.
        """

        if self.major < other.major:
            return True
        if self.major > other.major:
            return False

        if self.minor < other.minor:
            return True
        if self.minor > other.minor:
            return False

        if self.patch < other.patch:
            return True
        if self.patch > other.patch:
            return False

        if self.pre and not other.pre:
            return True
        if not self.pre and other.pre:
            return False

        if self.pre < other.pre:
            return True
        if self.pre > other.pre:
            return False

        return False


if __name__ == "__main__":
    import rich

    rich.print(f"{__file__}: {__doc__.strip()}")

    # Test: Version
    ver1 = Version("1.2.3")
    assert str(ver1) == "1.2.3"
    assert ver1.major == 1
    assert ver1.minor == 2
    assert ver1.patch == 3
    assert ver1.pre == ""
    assert ver1.build == ""

    # Test: Version with pre-release and build
    ver2 = Version("1.2.3-alpha+build")
    assert str(ver2) == "1.2.3-alpha+build"
    assert ver2.major == 1
    assert ver2.minor == 2
    assert ver2.patch == 3
    assert ver2.pre == "alpha"
    assert ver2.build == "build"

    # Test: Version comparison
    assert (ver1 == ver2) is False
    assert (ver1 != ver2) is True
    assert (ver1 > ver2) is True
    assert (ver1 < ver2) is False

    # Test: Version copy
    ver3 = Version(ver1)
    assert (ver1 == ver3) is True

    # Test: Version tuple
    ver4 = Version((1, 2, 3, "alpha", "build"))
    assert str(ver4) == "1.2.3-alpha+build"
    assert ver4.major == 1
    assert ver4.minor == 2
    assert ver4.patch == 3
    assert ver4.pre == "alpha"
    assert ver4.build == "build"
