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

"""Version numbering analysis and comparison module."""

from __future__ import annotations

import re
from typing import Self, overload

__all__ = ["Version"]


class Version:
    """Version analyzer."""

    major: int
    minor: int
    patch: int
    pre: str
    build: str

    @overload
    def __init__(self, version: str) -> None: ...

    @overload
    def __init__(self, version: Self) -> None: ...

    @overload
    def __init__(self, version: tuple) -> None: ...

    def __init__(self, version: str | Self | tuple) -> None:
        """Initialize the version analyzer.

        Args:
            version (str | Version | tuple): The version string.

        Raises:
            ValueError: Invalid version type.

        """
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
            if len(version) > 3:  # noqa: PLR2004
                self.pre = str(version[3])
            if len(version) > 4:  # noqa: PLR2004
                self.build = str(version[4])
        else:
            msg = "Invalid version type."
            raise ValueError(msg)  # noqa: TRY004

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
        return f"Version({self!s})"

    def __eq__(self, other: Self | object) -> bool:
        """Compare two versions for equality.

        Args:
            other (Version | object): The other version.

        Returns:
            bool: True if equal, False otherwise.

        """
        if not isinstance(other, Version):
            return False

        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
            and self.pre == other.pre
            and self.build == other.build
        )

    def __ne__(self, other: object) -> bool:
        """Compare two versions for inequality.

        Args:
            other (Version): The other version.

        Returns:
            bool: True if not equal, False otherwise.

        """
        return not self.__eq__(other)

    def __lt__(  # pylint: disable=R0911 # noqa: C901 PLR0911
        self,
        other: Self,
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
    # Test: Version.
    ver1 = Version("1.2.3")
    assert str(ver1) == "1.2.3"  # noqa: S101
    assert ver1.major == 1  # noqa: S101
    assert ver1.minor == 2  # noqa: S101 PLR2004
    assert ver1.patch == 3  # noqa: S101 PLR2004
    assert ver1.pre == ""  # noqa: S101
    assert ver1.build == ""  # noqa: S101

    # Test: Version with pre-release and build
    ver2 = Version("1.2.3-alpha+build")
    assert str(ver2) == "1.2.3-alpha+build"  # noqa: S101
    assert ver2.major == 1  # noqa: S101
    assert ver2.minor == 2  # noqa: S101 PLR2004
    assert ver2.patch == 3  # noqa: S101 PLR2004
    assert ver2.pre == "alpha"  # noqa: S101
    assert ver2.build == "build"  # noqa: S101

    # Test: Version comparison
    assert (ver1 == ver2) is False  # noqa: S101
    assert (ver1 != ver2) is True  # noqa: S101
    assert (ver1 > ver2) is True  # noqa: S101
    assert (ver1 < ver2) is False  # noqa: S101

    # Test: Version copy
    ver3 = Version(ver1)
    assert (ver1 == ver3) is True  # noqa: S101

    # Test: Version tuple
    ver4 = Version((1, 2, 3, "alpha", "build"))
    assert str(ver4) == "1.2.3-alpha+build"  # noqa: S101
    assert ver4.major == 1  # noqa: S101
    assert ver4.minor == 2  # noqa: S101 PLR2004
    assert ver4.patch == 3  # noqa: S101 PLR2004
    assert ver4.pre == "alpha"  # noqa: S101
    assert ver4.build == "build"  # noqa: S101
