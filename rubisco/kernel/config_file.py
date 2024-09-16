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

"""Rubisco config file loader."""

import json5 as json

from rubisco.config import (
    DEFAULT_CHARSET,
    GLOBAL_CONFIG_FILE,
    USER_CONFIG_FILE,
    WORKSPACE_CONFIG_FILE,
)
from rubisco.lib.log import logger
from rubisco.lib.variable import AutoFormatDict

__all__ = ["config_file"]

config_file = AutoFormatDict()

try:
    logger.info("Loading global configuration %s ...", GLOBAL_CONFIG_FILE)
    if GLOBAL_CONFIG_FILE.exists():
        with GLOBAL_CONFIG_FILE.open("r", encoding=DEFAULT_CHARSET) as f:
            config_file.merge(AutoFormatDict(json.load(f)))
except:  # pylint: disable=bare-except  # noqa: E722
    logger.warning(
        "Failed to load global configuration: %s",
        GLOBAL_CONFIG_FILE,
        exc_info=True,
    )

try:
    logger.info("Loading user configuration %s ...", USER_CONFIG_FILE)
    if USER_CONFIG_FILE.exists():
        with USER_CONFIG_FILE.open("r", encoding=DEFAULT_CHARSET) as f:
            config_file.merge(AutoFormatDict(json.load(f)))
except:  # pylint: disable=bare-except  # noqa: E722
    logger.warning(
        "Failed to load user configuration: %s",
        USER_CONFIG_FILE,
        exc_info=True,
    )

try:
    logger.info(
        "Loading workspace configuration %s ...",
        WORKSPACE_CONFIG_FILE,
    )
    if WORKSPACE_CONFIG_FILE.exists():
        with WORKSPACE_CONFIG_FILE.open("r", encoding=DEFAULT_CHARSET) as f:
            config_file.merge(AutoFormatDict(json.load(f)))
except:  # pylint: disable=bare-except  # noqa: E722
    logger.warning(
        "Failed to load workspace configuration: %s",
        WORKSPACE_CONFIG_FILE,
        exc_info=True,
    )
