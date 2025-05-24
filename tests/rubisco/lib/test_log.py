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

"""Test rubisco.lib.log module."""

from rubisco.lib.log import logger


def test_log() -> None:
    """Test the logging system."""
    logger.debug("Debug message.")
    logger.info("Info message.")
    logger.debug("Debug message.")
    logger.info("Info message.")
    logger.warning("Warning message.")
    logger.error("Error message.")
    logger.critical("Critical message.")
    try:
        msg = "Test exception."
        raise RuntimeError(msg)  # noqa: TRY301
    except RuntimeError:
        logger.exception("Exception message.")
        logger.warning("Warning with exception.", exc_info=True)
    logger.info("Done.")
