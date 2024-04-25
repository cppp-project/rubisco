# -*- coding: utf-8 -*-
# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2024 The C++ Plus Project.
# This file is part of the repoutils.
#
# repoutils is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# repoutils is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Path resolver with globbing support.
"""

import glob
from pathlib import Path

__all__ = ["resolve_path", "glob_path"]


def resolve_path(path: Path, absolute_only: bool = True) -> Path:
    """Resolve a path with globbing support.

    Args:
        path (Path): Path to resolve.
        absolute_only (bool): Absolute path only instead of resolve.
            Defaults to True.

    Returns:
        Path: Resolved path.
    """

    res = path.expanduser().absolute()
    if absolute_only:
        return res
    return res.resolve()


def glob_path(path: Path, absolute_only: bool = True) -> list[Path]:
    """Resolve a path and globbing it.

    Args:
        path (Path): Path to resolve.
        absolute_only (bool, optional): Absolute path only instead of resolve.
            Defaults to False.

    Returns:
        list[Path]: List of resolved paths.
    """

    res = glob.glob(str(resolve_path(path, absolute_only)))
    return [Path(p).absolute() for p in res]
