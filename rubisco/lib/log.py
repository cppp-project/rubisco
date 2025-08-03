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

import rich
import rich.logging

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
    _init_log_handler(ru_logger)
    return ru_logger


def _init_log_handler(logger_: logging.Logger) -> None:
    logger_.addHandler(logging.NullHandler())

    if "--log" in sys.argv:
        if not Path(LOG_FILE).parent.exists():
            LOG_FILE.parent.mkdir(exist_ok=True)
        handler = logging.FileHandler(LOG_FILE, encoding=DEFAULT_CHARSET)
        handler.setLevel(LOG_LEVEL)

        formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_TIME_FORMAT)
        handler.setFormatter(formatter)

        logger_.addHandler(handler)
    if "--debug" in sys.argv:  # Don't use argparse here.
        handler = rich.logging.RichHandler(
            level=LOG_LEVEL,
            console=rich.get_console(),
        )
        logger_.addHandler(handler)


# The global logger.
logger = rubisco_get_logger()
