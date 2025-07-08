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

"""Rubisco git API.

This module provides a basic git API.
"""

from rubisco.kernel.git import (
    git_branch_set_upstream,
    git_clone,
    git_get_remote,
    git_has_remote,
    git_set_remote,
    git_update,
    is_git_repo,
)

__all__ = [
    "git_branch_set_upstream",
    "git_clone",
    "git_get_remote",
    "git_has_remote",
    "git_set_remote",
    "git_update",
    "is_git_repo",
]
