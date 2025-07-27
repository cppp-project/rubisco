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

"""Utils for Rubisco project."""

from pathlib import Path

from beartype import beartype

from rubisco.config import USER_REPO_CONFIG
from rubisco.kernel.config_loader import SUPPORTED_EXTS

__all__ = ["is_rubisco_project"]


@beartype
def is_rubisco_project(project_dir: Path) -> bool:
    """Check if the given directory is a Rubisco project.

    Args:
        project_dir (Path): The path to the project directory.

    Returns:
        bool: True if the directory is a Rubisco project, False otherwise.

    """
    path = project_dir / USER_REPO_CONFIG
    if path.is_file():
        return True

    return any(path.with_suffix(ext).is_file() for ext in SUPPORTED_EXTS)
