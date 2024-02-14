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

APP_DEFAULT_NAME = "cppp-repoutils"
APP_VERSION = (0, 1, 0)
TEXT_DOMAIN = APP_DEFAULT_NAME
REPO_PROFILE_NAME = "cppp-repo.json"
DEFAULT_CHARSET = "UTF-8"
DEFAULT_IGNFILE_NAME = ".cpppignore"
DEFAULT_LANGUAGE = "en_US"
LOG_FILE = "cppp-repoutils.log"
LOG_FORMAT = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
LOG_LEVEL = "DEBUG"
TIMEOUT = 15
COPY_BUFSIZE_WINDOWS = 1024 * 1024
COPY_BUFSIZE_OTHERS = 64 * 1024
WGET_BUFSIZE = 8 * 1024
