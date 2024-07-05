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
Load module from path dynamically. To perfect fking Python import system.
"""


import importlib.util
from pathlib import Path
from types import ModuleType

__all__ = ["import_module_from_path"]


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
        raise FileNotFoundError(path)

    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    else:
        raise ImportError(path)

    return module
