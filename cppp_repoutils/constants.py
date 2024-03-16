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
from pathlib import Path

from cppp_repoutils.config import (
    APP_DEFAULT_NAME,
    APP_VERSION,
    COPY_BUFSIZE_OTHERS,
    COPY_BUFSIZE_WINDOWS,
    DEFAULT_CHARSET,
    DEFAULT_IGNFILE_NAME,
    LOG_FILE,
    LOG_FORMAT,
    LOG_LEVEL,
    REPO_PROFILE_NAME,
    SETUP_TEMP_CACHE_NAME,
    TEXT_DOMAIN,
    TIMEOUT,
    MINIMUM_PYTHON_VERSION,
    WGET_BUFSIZE,
    PACKAGE_TYPE_GIT,
    PACKAGE_TYPE_ARCHIVE,
    PACKAGE_TYPE_VIRTUAL,
    PACKAGE_KEY_PATH,
    PACKAGE_KEY_TYPE,
    PACKAGE_KEY_REMOTE_URL,
    PACKAGE_KEY_GIT_BRANCH,
    PACKAGE_KEY_ARCHIVE_TYPE,
    PACKAGE_KEY_NAME,
    PACKAGE_KEY_VERSION,
    PACKAGE_KEY_DESC,
    PACKAGE_KEY_AUTHORS,
    PACKAGE_KEY_HOMEPAGE,
    PACKAGE_KEY_LICENSE,
    PACKAGE_KEY_SUBPKGS,
    PACKAGE_KEY_TAGS
)

__all__ = [
    "APP_NAME",
    "APP_VERSION",
    "TEXT_DOMAIN",
    "DEFAULT_CHARSET",
    "DEFAULT_IGNFILE",
    "LOG_FILE",
    "LOG_FORMAT",
    "LOG_LEVEL",
    "TIMEOUT",
    "MINIMUM_PYTHON_VERSION",
    "WGET_BUFSIZE",
    "APP_VERSION_STRING",
    "COPY_BUFSIZE",
    "PROGRAM_PATH",
    "PROGRAM_DIR",
    "PYTHON_PATH",
    "REPO_PROFILE",
    "SETUP_TEMP_CACHE",
    "RESOURCE_PATH",
    "STDOUT_IS_TTY",
    "IS_PACKED",
    "PACKAGE_TYPE_GIT",
    "PACKAGE_TYPE_ARCHIVE",
    "PACKAGE_TYPE_VIRTUAL",
    "PACKAGE_KEY_PATH",
    "PACKAGE_KEY_TYPE",
    "PACKAGE_KEY_REMOTE_URL",
    "PACKAGE_KEY_GIT_BRANCH",
    "PACKAGE_KEY_ARCHIVE_TYPE",
    "PACKAGE_KEY_NAME",
    "PACKAGE_KEY_VERSION",
    "PACKAGE_KEY_DESC",
    "PACKAGE_KEY_AUTHORS",
    "PACKAGE_KEY_HOMEPAGE",
    "PACKAGE_KEY_LICENSE",
    "PACKAGE_KEY_SUBPKGS",
    "PACKAGE_KEY_TAGS"
]

APP_VERSION_STRING: str = ".".join(map(str, APP_VERSION))  # (X.X.X)
COPY_BUFSIZE = COPY_BUFSIZE_WINDOWS if os.name == "nt" else COPY_BUFSIZE_OTHERS
PROGRAM_PATH: Path = Path(sys.argv[0]).resolve()
PROGRAM_DIR: Path = PROGRAM_PATH.parent.absolute()
PYTHON_PATH: Path | None = Path(sys.executable).resolve()
REPO_PROFILE: Path = Path(REPO_PROFILE_NAME)
SETUP_TEMP_CACHE: Path = Path(SETUP_TEMP_CACHE_NAME)
DEFAULT_IGNFILE: Path = Path(DEFAULT_IGNFILE_NAME)
RESOURCE_PATH: Path = Path(getattr(sys, "_MEIPASS", PROGRAM_DIR)).absolute()
STDOUT_IS_TTY = sys.stdout.isatty()

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

PYTHON_PATH = PYTHON_PATH if not IS_PACKED else None

# Detect app name.
APP_NAME: str
match (PROGRAM_PATH.stem):
    case "cppp-compress":
        APP_NAME = "cppp-compress"
    case _:
        APP_NAME = APP_DEFAULT_NAME

if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    for name in __all__:
        print(f"{name}: {globals()[name]}")
