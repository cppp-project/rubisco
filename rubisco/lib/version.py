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
from typing import TYPE_CHECKING, Self, overload

if TYPE_CHECKING:
    from collections.abc import Sequence

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
    def __init__(self, version: tuple[int, int, int]) -> None: ...

    @overload
    def __init__(self, version: tuple[int, int, int, str]) -> None: ...

    @overload
    def __init__(self, version: tuple[int, int, int, str, str]) -> None: ...

    def __init__(
        self,
        version: (
            str
            | Self
            | tuple[int, int, int]
            | tuple[int, int, int, str]
            | tuple[int, int, int, str, str]
            | Sequence[int | str]
        ),
    ) -> None:
        """Initialize the version analyzer.

        Args:
            version (str | Version | tuple | Iterable[int | str]): The version
                string or tuple. If a tuple, it should be in the form of
                (major, minor, patch, pre-release[optional], build[optional]).

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
        else:
            self.major = int(version[0])
            self.minor = int(version[1])
            self.patch = int(version[2])
            self.pre = str(version[3]) if len(version) > 3 else ""  # noqa: PLR2004
            self.build = str(version[4]) if len(version) > 4 else ""  # noqa: PLR2004

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

    def __format__(self, format_spec: str) -> str:
        """Format the version string.

        Args:
            format_spec (str): The format spec.

        Returns:
            str: The formatted version string.

        """
        return self.__str__()

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


class TestVersion:
    """Test the Version class."""

    def test_version(self) -> None:
        """Test the Version class basic usage."""
        ver = Version("1.2.3")
        if str(ver) != "1.2.3":
            raise AssertionError
        if ver.major != 1 or ver.minor != 2 or ver.patch != 3:  # noqa: PLR2004
            raise AssertionError
        if ver.pre != "" or ver.build != "":
            raise AssertionError

    def test_version_with_pre_release(self) -> None:
        """Test the Version class with pre-release."""
        ver = Version("1.2.3-alpha")
        if str(ver) != "1.2.3-alpha":
            raise AssertionError
        if ver.major != 1 or ver.minor != 2 or ver.patch != 3:  # noqa: PLR2004
            raise AssertionError
        if ver.pre != "alpha" or ver.build != "":
            raise AssertionError

        ver = Version("1.2.3-alpha+build")
        if str(ver) != "1.2.3-alpha+build":
            raise AssertionError
        if ver.major != 1 or ver.minor != 2 or ver.patch != 3:  # noqa: PLR2004
            raise AssertionError
        if ver.pre != "alpha" or ver.build != "build":
            raise AssertionError
        ver = Version("1.2.3+build")
        if str(ver) != "1.2.3+build":
            raise AssertionError
        if ver.major != 1 or ver.minor != 2 or ver.patch != 3:  # noqa: PLR2004
            raise AssertionError
        if ver.pre != "" or ver.build != "build":
            raise AssertionError

    def test_version_comparison(self) -> None:
        """Test the Version class comparison."""
        ver1 = Version("1.2.3")
        ver2 = Version("1.2.3-alpha+build")
        if (ver1 == ver2) is True:
            raise AssertionError
        if (ver1 != ver2) is False:
            raise AssertionError
        if (ver1 > ver2) is False:
            raise AssertionError
        if (ver1 < ver2) is True:
            raise AssertionError

    def test_version_copy(self) -> None:
        """Test the Version class copy."""
        ver1 = Version("1.2.3-alpha+build")
        ver2 = Version(ver1)
        if ver1 != ver2:
            raise AssertionError

    def test_version_tuple(self) -> None:
        """Test the Version class with tuple."""
        ver = Version((1, 2, 3, "alpha", "build"))
        if str(ver) != "1.2.3-alpha+build":
            raise AssertionError
        if ver.major != 1 or ver.minor != 2 or ver.patch != 3:  # noqa: PLR2004
            raise AssertionError
        if ver.pre != "alpha" or ver.build != "build":
            raise AssertionError
