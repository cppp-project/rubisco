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
Module configuration.
"""

__all__ = [
    "APP_NAME",
    "APP_VERSION",
    "TEXT_DOMAIN",
    "REPO_PROFILE_NAME",
    "DIST_IGNORE_FILE_NAME",
    "LOG_LEVEL",
    "LOG_FILE",
    "LOG_FORMAT",
    "IS_DEV",
    "__author__",
    "__copyright__",
    "__license__",
    "__maintainer__",
    "__url__",
]

# ====================================== Basic configurations ======================================

# Application name.
APP_NAME: str = "cppp-repoutils"

# Application version.
APP_VERSION: tuple[int, int, int] = (0, 1, 0)

# Text domain
TEXT_DOMAIN: str = APP_NAME

# Repository profile file.
REPO_PROFILE_NAME: str = "cppp-repo.json"

# Ignore file for dist.
DIST_IGNORE_FILE_NAME: str = ".cppprepoignore"

# Default charset for text files.
DEFAULT_CHARSET: str = "UTF-8"

# Log level.
LOG_LEVEL: str = "DEBUG"

# Log file.
LOG_FILE: str = "cppp-repoutils.log"

# Log format.
LOG_FORMAT: str = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"

# Release status.
IS_DEV: bool = True

__author__ = "ChenPi11"
__copyright__ = "Copyright (C) 2024 The C++ Plus Project"
__license__ = "GPLv3-or-later"
__maintainer__ = "ChenPi11"
__url__ = "https://github.com/cppp-project/cppp-repoutils"
