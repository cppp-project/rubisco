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

"""Logging system."""

import logging
import sys
from pathlib import Path

from rubisco.config import (
    APP_NAME,
    DEFAULT_CHARSET,
    LOG_FILE,
    LOG_FORMAT,
    LOG_LEVEL,
    LOG_TIME_FORMAT,
)

__all__ = ["logger", "rubisco_get_logger"]


def rubisco_get_logger(name: str = APP_NAME) -> logging.Logger:
    """Get the logger.

    Args:
        name (str, optional): The name of the logger. Defaults to APP_NAME.

    Returns:
        logging.Logger: The logger.

    """
    ru_logger = logging.getLogger(name)
    ru_logger.setLevel(LOG_LEVEL)
    return ru_logger


# The global logger.
logger = rubisco_get_logger()


if "--log" in sys.argv:
    if not Path(LOG_FILE).parent.exists():
        LOG_FILE.parent.mkdir(exist_ok=True)
    logger_handler = logging.FileHandler(LOG_FILE, encoding=DEFAULT_CHARSET)
    logger_handler.setLevel(LOG_LEVEL)

    logger_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_TIME_FORMAT)
    logger_handler.setFormatter(logger_formatter)

    logger.addHandler(logger_handler)
else:
    logger.addHandler(logging.NullHandler())

if "--debug" in sys.argv:  # Don't use argparse here.
    import rich
    import rich.logging

    logger_handler = rich.logging.RichHandler(
        level=LOG_LEVEL,
        console=rich.get_console(),
    )
    logger_formatter = logging.Formatter(LOG_FORMAT)
    logger.addHandler(logger_handler)
