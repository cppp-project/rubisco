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

"""Test rubisco.lib.version module."""

import pytest

from rubisco.lib.version import Version


class TestVersion:
    """Test the Version class."""

    def test_version(self) -> None:
        """Test the Version class basic usage."""
        ver = Version("1.2.3")
        if str(ver) != "1.2.3":
            pytest.fail("Version string is not correct.")
        if ver.major != 1 or ver.minor != 2 or ver.patch != 3:  # noqa: PLR2004
            pytest.fail("Version number is not correct.")
        if ver.pre != "" or ver.build != "":
            pytest.fail("Version pre-release or build is not correct.")

    def test_version_with_pre_release(self) -> None:
        """Test the Version class with pre-release."""
        ver = Version("1.2.3-alpha")
        if str(ver) != "1.2.3-alpha":
            pytest.fail("Version string is not correct.")
        if ver.major != 1 or ver.minor != 2 or ver.patch != 3:  # noqa: PLR2004
            pytest.fail("Version number is not correct.")
        if ver.pre != "alpha" or ver.build != "":
            pytest.fail("Version pre-release or build is not correct.")

        ver = Version("1.2.3-alpha+build")
        if str(ver) != "1.2.3-alpha+build":
            pytest.fail("Version string is not correct.")
        if ver.major != 1 or ver.minor != 2 or ver.patch != 3:  # noqa: PLR2004
            pytest.fail("Version number is not correct.")
        if ver.pre != "alpha" or ver.build != "build":
            pytest.fail("Version pre-release or build is not correct.")
        ver = Version("1.2.3+build")
        if str(ver) != "1.2.3+build":
            pytest.fail("Version string is not correct.")
        if ver.major != 1 or ver.minor != 2 or ver.patch != 3:  # noqa: PLR2004
            pytest.fail("Version number is not correct.")
        if ver.pre != "" or ver.build != "build":
            pytest.fail("Version pre-release or build is not correct.")

    def test_version_comparison(self) -> None:
        """Test the Version class comparison."""
        ver1 = Version("1.2.3")
        ver2 = Version("1.2.3-alpha+build")
        if (ver1 == ver2) is True:
            pytest.fail("Version comparison is not correct.")
        if (ver1 != ver2) is False:
            pytest.fail("Version comparison is not correct.")
        if (ver1 > ver2) is False:
            pytest.fail("Version comparison is not correct.")
        if (ver1 < ver2) is True:
            pytest.fail("Version comparison is not correct.")

    def test_version_copy(self) -> None:
        """Test the Version class copy."""
        ver1 = Version("1.2.3-alpha+build")
        ver2 = Version(ver1)
        if ver1 != ver2:
            pytest.fail("Version copy is not correct.")

    def test_version_tuple(self) -> None:
        """Test the Version class with tuple."""
        ver = Version((1, 2, 3, "alpha", "build"))
        if str(ver) != "1.2.3-alpha+build":
            pytest.fail("Version string is not correct.")
        if ver.major != 1 or ver.minor != 2 or ver.patch != 3:  # noqa: PLR2004
            pytest.fail("Version number is not correct.")
        if ver.pre != "alpha" or ver.build != "build":
            pytest.fail("Version pre-release or build is not correct.")
