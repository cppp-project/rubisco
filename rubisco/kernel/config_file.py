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

from pathlib import Path

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


def _load_json(file: Path, envname: str) -> None:
    try:
        logger.info("Loading global configuration %s ...", file)
        if file.exists():
            with file.open("r", encoding=DEFAULT_CHARSET) as f:
                config_file.merge(AutoFormatDict(json.load(f)))
    except:  # pylint: disable=bare-except  # noqa: E722
        logger.warning(
            "Failed to load %s configuration: %s",
            envname,
            file,
            exc_info=True,
        )


_load_json(GLOBAL_CONFIG_FILE, "global")
_load_json(USER_CONFIG_FILE, "user")
_load_json(WORKSPACE_CONFIG_FILE, "workspace")
