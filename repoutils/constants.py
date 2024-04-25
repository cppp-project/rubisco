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
Constants for the repoutils module.
"""

from pathlib import Path
import sys
import os
from repoutils.lib.command import command
from repoutils.lib.version import Version
from repoutils.config import (
    APP_NAME,
    APP_VERSION,
    DEFAULT_CHARSET,
    USER_PROFILE_DIR,
    MIRRORLIST_FILE,
    LOG_FILE,
    LOG_FORMAT,
    LOG_LEVEL,
    REPO_PROFILE,
    TEXT_DOMAIN,
    TIMEOUT,
    COPY_BUFSIZE_WINDOWS,
    COPY_BUFSIZE_UNIX,
    MINIMUM_PYTHON_VERSION
)

__all__ = [
    "APP_NAME",
    "APP_VERSION",
    "DEFAULT_CHARSET",
    "MINIMUM_PYTHON_VERSION",
    "USER_PROFILE_DIR",
    "MIRRORLIST_FILE",
    "LOG_FILE",
    "LOG_FORMAT",
    "LOG_LEVEL",
    "REPO_PROFILE",
    "TEXT_DOMAIN",
    "TIMEOUT",
    "COPY_BUFSIZE",
    "STDOUT_IS_TTY",
    "PROGRAM_PATH",
    "PYTHON_PATH",
    "IS_PACKED",
    "REPOUTILS_COMMAND",
]

APP_VERSION = Version(APP_VERSION)
MINIMUM_PYTHON_VERSION = Version(MINIMUM_PYTHON_VERSION)
USER_PROFILE_DIR = (Path.home() / USER_PROFILE_DIR).absolute()  # ~/.repoutils

# ~/.repoutils/mirrorlist.json
MIRRORLIST_FILE = USER_PROFILE_DIR / MIRRORLIST_FILE

# We don't need to absolute the path because repoutils supports '--root'
# option.
LOG_FILE = Path(LOG_FILE)
REPO_PROFILE = Path(REPO_PROFILE)
COPY_BUFSIZE = COPY_BUFSIZE_WINDOWS if os.name == "nt" else COPY_BUFSIZE_UNIX
STDOUT_IS_TTY = sys.stdout.isatty()
PROGRAM_PATH: Path = Path(sys.argv[0]).resolve()
PYTHON_PATH: Path | None = Path(sys.executable).resolve()

# Is packed, if true, it means that the program is running in a packed
# environment.
# (e.g. PyInstaller)
IS_PACKED = (
    getattr(sys, "frozen", False)
    or hasattr(sys, "_MEIPASS")  # PyInstaller
    or PROGRAM_PATH.suffix == ".exe"  # Windows
    or PROGRAM_PATH.suffix == ".app"  # macOS
    or PROGRAM_PATH.suffix == ".so"
    and PROGRAM_PATH.parent.name == "__nuitka__"  # Nuitka
    or not PYTHON_PATH.exists()
)

# The command line that can execute repoutils.
if IS_PACKED:
    REPOUTILS_COMMAND = command(str(PROGRAM_PATH))
else:
    REPOUTILS_COMMAND = command([str(PYTHON_PATH), str(PROGRAM_PATH)])
