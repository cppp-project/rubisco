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

"""Load module from path dynamically.

To perfect fking Python import system.
"""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

from rubisco.lib.exceptions import RUNotRubiscoExtensionError


def import_module_from_path(path: Path) -> ModuleType:
    """Load module from path.

    Args:
        path (Path): Path to module.

    Returns:
        ModuleType: Module object.

    Raises:
        FileNotFoundError: If the path does not exist or is a directory
            without `__init__.py`.
        ImportError: If the module cannot be loaded.

    """
    if path.is_dir():
        path = path / "__init__.py"

    if not path.exists():
        raise RUNotRubiscoExtensionError(str(path))

    paths = [
        str(path.parent.absolute()),
        str(path.parent.parent.absolute()),
    ]
    spec = importlib.util.spec_from_file_location(
        path.stem,
        path,
        submodule_search_locations=paths,
    )
    if spec:
        old_path = sys.path
        try:
            sys.path.extend(paths)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore[union-attr]
        finally:
            sys.path = old_path
    else:
        raise ImportError(path)

    return module


def test_import_file_module() -> None:
    """Test import a single-file module."""
    module = import_module_from_path(Path("tests/test_module.py"))
    if module.TEST != "test":
        raise AssertionError


def test_import_package_module() -> None:
    """Test import a package module."""
    module = import_module_from_path(Path("tests/test_pkg_module"))
    if module.TEST != "test" or module.TEST2 != "test":
        raise AssertionError


def test_import_not_found() -> None:
    """Test import a not found module."""
    pytest.raises(
        RUNotRubiscoExtensionError,
        import_module_from_path,
        Path("/_Not_Found_"),
    )
