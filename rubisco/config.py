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
Module configuration.
"""

import os
import sys
from pathlib import Path

from rubisco.lib.command import command
from rubisco.lib.version import Version

# Application basic configurations.
APP_NAME = "rubisco"
APP_VERSION = Version((0, 1, 0))
MINIMUM_PYTHON_VERSION = Version((3, 10, 0))

# I18n configurations.
TEXT_DOMAIN = APP_NAME
DEFAULT_CHARSET = "UTF-8"

# Miscellaneous configurations.
TIMEOUT = 15
COPY_BUFSIZE = 1024 * 1024 if os.name == "nt" else 64 * 1024

# Lib onfigurations.
WORKSPACE_LIB_DIR = Path(".rubisco")
WORKSPACE_CONFIG_DIR = WORKSPACE_LIB_DIR
WORKSPACE_CONFIG_FILE = WORKSPACE_LIB_DIR / "config.json"
WORKSPACE_EXTENTIONS_DIR = WORKSPACE_LIB_DIR / "extentions"
USER_REPO_CONFIG = Path("repo.json")
if os.name == "nt":
    local_appdata = Path(os.getenv("LOCALAPPDATA"))
    if not local_appdata:
        local_appdata = Path("~/AppData/Loacal").expanduser()
    USER_LIB_DIR = Path(local_appdata) / "rubisco"
    USER_CONFIG_DIR = Path(local_appdata) / "rubisco"
else:
    USER_LIB_DIR = Path("~/.local/rubisco").expanduser()
    USER_CONFIG_DIR = Path("~/.config/rubisco").expanduser()
USER_CONFIG_FILE = USER_CONFIG_DIR / "config.json"
USER_EXTENTIONS_DIR = USER_LIB_DIR / "extentions"
# Will override in Windows later.
GLOBAL_LIB_DIR = Path("/usr/local/lib/rubisco")
GLOBAL_CONFIG_DIR = Path("/etc/rubisco")
GLOBAL_CONFIG_FILE = GLOBAL_CONFIG_DIR / "config.json"
GLOBAL_EXTENTIONS_DIR = GLOBAL_LIB_DIR / "extentions"


# Logging configurations.
# We don't need to absolute the path because rubisco supports '--root'
# option.
LOG_FILE = WORKSPACE_LIB_DIR / "rubisco.log"
LOG_FORMAT = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
LOG_REGEX = r"\[(.*)\] \[(.*)\] \[(.*)\] (.*)"
LOG_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_LEVEL = "DEBUG"
DEFAULT_LOG_KEEP_LINES = 5000


# Constants that are not configurable.
STDOUT_IS_TTY = sys.stdout.isatty()
PROGRAM_PATH: Path = Path(sys.argv[0]).resolve()
if not sys.argv[0]:
    PROGRAM_PATH = Path(__file__).resolve().parent

PYTHON_PATH: Path | None = Path(sys.executable).resolve()
# If the program is running in a packed environment. (e.g. PyInstaller)
IS_PACKED = getattr(sys, "frozen", False) or hasattr(sys, "_MEIPASS")

if IS_PACKED:
    RUBISCO_COMMAND = command(str(PROGRAM_PATH))
    PYTHON_PATH = None
else:
    RUBISCO_COMMAND = command([str(PYTHON_PATH), str(PROGRAM_PATH)])

PROGRAM_DIR: Path = PROGRAM_PATH.parent.absolute()

if os.name == "nt":  # On Windows.
    GLOBAL_LIB_DIR = PROGRAM_DIR
    GLOBAL_CONFIG_DIR = PROGRAM_DIR / "config"
    GLOBAL_CONFIG_FILE = GLOBAL_CONFIG_DIR / "config.json"
    GLOBAL_EXTENTIONS_DIR = GLOBAL_LIB_DIR / "extentions"
