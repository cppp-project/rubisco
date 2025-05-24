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

"""Test rubisco.lib.load_module module."""

from pathlib import Path

import pytest

from rubisco.lib.exceptions import RUNotRubiscoExtensionError
from rubisco.lib.load_module import import_module_from_path


class TestLoadModule:
    """Test load module from path."""

    def test_import_file_module(self) -> None:
        """Test import a single-file module."""
        module = import_module_from_path(Path("tests/test_module.py"))
        if module.TEST != "test":
            raise AssertionError

    def test_import_package_module(self) -> None:
        """Test import a package module."""
        module = import_module_from_path(Path("tests/test_pkg_module"))
        if module.TEST != "test" or module.TEST2 != "test":
            raise AssertionError

    def test_import_not_found(self) -> None:
        """Test import a not found module."""
        pytest.raises(
            RUNotRubiscoExtensionError,
            import_module_from_path,
            Path("/_Not_Found_"),
        )
