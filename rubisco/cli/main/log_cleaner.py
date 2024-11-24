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

"""Utils for clean log. Called by the main entry point."""

from rubisco.config import (
    DEFAULT_CHARSET,
    DEFAULT_LOG_KEEP_LINES,
    LOG_FILE,
    PIP_LOG_FILE,
)
from rubisco.lib.log import logger
from rubisco.lib.pathlib import Path

__all__ = ["clean_log"]


def clean_log() -> None:
    """Clean the log file."""
    if not LOG_FILE.exists():
        return
    try:
        line_count = 0
        with Path.open(LOG_FILE, "r+", encoding=DEFAULT_CHARSET) as f:
            for _line in f:
                line_count += 1
                if line_count > DEFAULT_LOG_KEEP_LINES:
                    f.seek(0)
                    f.truncate()
                    return
    except:  # pylint: disable=bare-except  # noqa: E722
        logger.warning("Failed to clean log file.", exc_info=True)

    try:
        line_count = 0
        with Path.open(PIP_LOG_FILE, "r+", encoding=DEFAULT_CHARSET) as f:
            for _line in f:
                line_count += 1
                if line_count > DEFAULT_LOG_KEEP_LINES:
                    f.seek(0)
                    f.truncate()
                    return
    except:  # pylint: disable=bare-except  # noqa: E722 S110
        pass  # Logging a log file exception?
