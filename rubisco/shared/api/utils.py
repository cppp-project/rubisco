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

"""Rubisco miscellaneous utils."""

from rubisco.lib.command import command, expand_cmdlist
from rubisco.lib.fileutil import (
    TemporaryObject,
    check_file_exists,
    copy_recursive,
    find_command,
    glob_path,
    human_readable_size,
    resolve_path,
    rm_recursive,
)
from rubisco.lib.load_module import import_module_from_path
from rubisco.lib.process import Process
from rubisco.lib.stack import Stack
from rubisco.lib.version import Version
from rubisco.lib.wget import wget

__all__ = [
    "Process",
    "Stack",
    "TemporaryObject",
    "Version",
    "check_file_exists",
    "command",
    "copy_recursive",
    "expand_cmdlist",
    "find_command",
    "glob_path",
    "human_readable_size",
    "import_module_from_path",
    "resolve_path",
    "rm_recursive",
    "wget",
]
