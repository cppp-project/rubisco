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

"""Test for maintainer class."""

import pytest

from rubisco.kernel.project_config.maintainer import Maintainer


class TestMaintainer:
    """Test for maintainer class."""

    def test_name(self) -> None:
        """Test for maintainer name."""
        m = Maintainer.parse("Cutton Eye Joe")
        if m != Maintainer(name="Cutton Eye Joe", email=None, homepage=None):
            pytest.fail("Name parse failed.")

    def test_with_email(self) -> None:
        """Test for maintainer name with email."""
        m = Maintainer.parse("Peter Griffin <griffin@example.com>")
        if m != Maintainer(
            name="Peter Griffin",
            email="griffin@example.com",
            homepage=None,
        ):
            pytest.fail("Name with email parse failed.")

    def test_with_email_homepage(self) -> None:
        """Test for maintainer name with email and homepage."""
        m = Maintainer.parse(
            "The C++ Plus Project <cpppteam@"
            "email.cn> (https://cppp-project.github.io)",
        )
        if m != Maintainer(
            name="The C++ Plus Project",
            email="cpppteam@email.cn",
            homepage="https://cppp-project.github.io",
        ):
            pytest.fail("Name with email and homepage parse failed.")

    def test_with_homepage(self) -> None:
        """Test for maintainerr name with homepage."""
        m = Maintainer.parse("ChenPi11 (https://chenpi11.github.io)")
        if m != Maintainer(
            name="ChenPi11",
            email=None,
            homepage="https://chenpi11.github.io",
        ):
            pytest.fail("Name with homepage parse failed.")
