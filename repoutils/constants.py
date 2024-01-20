# -*- coding: utf-8 -*-
# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2024 The C++ Plus Project.
# This file is part of the cppp-repoutils.
#
# cppp-repoutils is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# cppp-repoutils is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Module constants load from module configuration.
"""

import os
import sys
from typing import Optional
from pathlib import Path

from repoutils.config import (
    APP_NAME,
    APP_VERSION,
    TEXT_DOMAIN,
    REPO_PROFILE_NAME,
    DIST_IGNORE_FILE_NAME,
    DEFAULT_CHARSET,
    LOG_LEVEL,
    LOG_FILE,
    LOG_FORMAT,
    IS_DEV,
    __author__,
    __copyright__,
    __license__,
    __maintainer__,
    __url__,
)

__all__ = [
    "APP_NAME",
    "APP_VERSION",
    "TEXT_DOMAIN",
    "DEFAULT_CHARSET",
    "APP_VERSION_STRING",
    "REPO_PROFILE",
    "DIST_IGNORE_FILE",
    "PROGRAM_PATH",
    "PYTHON_PATH",
    "CWD",
    "PROGRAM_DIR",
    "IS_PACKED",
    "RESOURCE_PATH",
    "LOG_LEVEL",
    "LOG_FILE",
    "LOG_FORMAT",
    "IS_DEV",
    "STDOUT_IS_TTY",
]


# Application version string. (X.X.X)
APP_VERSION_STRING: str = ".".join(map(str, APP_VERSION))

# Repository profile file path.
REPO_PROFILE: Path = Path(REPO_PROFILE_NAME)

# Ignore file for dist.
DIST_IGNORE_FILE: Path = Path(DIST_IGNORE_FILE_NAME)

# Program file path.
PROGRAM_PATH: Path = Path(sys.argv[0]).resolve()
# We resolve the program path because we need to get the real path of the program file.
# For example, if the program is a symbolic link, don't resolve it will cause the program
# cannot find the real profile file.

if not os.path.exists(sys.argv[0]):
    # If the program file is not exists (e.g. Python interpreter), we need to use this file's
    # path as the program file path.
    PROGRAM_PATH = Path(__file__).resolve()

# Python interpreter path.
PYTHON_PATH: Optional[Path] = Path(sys.executable).resolve()

# Current working directory.
CWD: Path = Path(os.path.curdir)
# Don't resolve it, because we need to get the current working directory.

# Directory of this program.
PROGRAM_DIR: Path = PROGRAM_PATH.parent.absolute()
# We use the parent directory of the program file as the program directory.


# Is packed, if true, it means that the program is running in a packed environment.
# (e.g. PyInstaller)
IS_PACKED: bool = False


IS_PACKED = (
    IS_PACKED or getattr(sys, "frozen", False) or hasattr(sys, "_MEIPASS")
)  # PyInstaller
IS_PACKED = IS_PACKED or PROGRAM_PATH.suffix == ".exe"  # Windows
IS_PACKED = IS_PACKED or PROGRAM_PATH.suffix == ".app"  # macOS
IS_PACKED = (
    IS_PACKED
    or PROGRAM_PATH.suffix == ".so"
    and PROGRAM_PATH.parent.name == "__nuitka__"
)  # Nuitka
IS_PACKED = (
    IS_PACKED or not PYTHON_PATH.is_file()
)  # If Python interpreter is not found, it means that the program is packed.

if IS_PACKED:
    PYTHON_PATH = None  # Packed, so no Python interpreter.

# Resource path when packed.
RESOURCE_PATH: Path = Path(
    getattr(sys, "_MEIPASS", PROGRAM_DIR)
).resolve()  # PyInstaller

# Check if stdout is a tty.
STDOUT_IS_TTY = sys.stdout.isatty()

if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    for name in __all__:
        print(f"{name}: {globals()[name]}")
