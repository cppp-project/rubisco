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
Logging system.
"""

import logging
import os
import sys
from pathlib import Path

from repoutils.config import (APP_NAME, DEFAULT_CHARSET, LOG_FILE, LOG_FORMAT,
                              LOG_LEVEL)

__all__ = ["logger"]

# The global logger.
logger = logging.getLogger(APP_NAME)

# Initialize the global logger.

logger.setLevel(LOG_LEVEL)

if not Path(LOG_FILE).parent.exists():
    os.makedirs(Path(LOG_FILE).parent, exist_ok=True)
logger_handler = logging.FileHandler(LOG_FILE, encoding=DEFAULT_CHARSET)
logger_handler.setLevel(LOG_LEVEL)

logger_formatter = logging.Formatter(LOG_FORMAT)
logger_handler.setFormatter(logger_formatter)

logger.addHandler(logger_handler)

if "--debug" in sys.argv:  # Don't use argparse here.
    import colorama

    colorama.init(autoreset=True)

    class _DebugStreamHandler(logging.StreamHandler):
        def emit(self, record: logging.LogRecord):
            stream = sys.stdout
            if stream.isatty():
                match record.levelno:
                    case logging.DEBUG:
                        stream.write(colorama.Fore.CYAN)
                    case logging.INFO:
                        stream.write(colorama.Fore.LIGHTWHITE_EX)
                    case logging.WARNING:
                        stream.write(colorama.Fore.LIGHTYELLOW_EX)
                    case logging.ERROR:
                        stream.write(colorama.Fore.LIGHTRED_EX)
                    case logging.CRITICAL:
                        stream.write(colorama.Fore.RED)
            super().emit(record)
            if stream.isatty():
                stream.write(colorama.Fore.RESET)
            stream.flush()

    logger_handler = _DebugStreamHandler(sys.stderr)
    logger_handler.setLevel(LOG_LEVEL)

    logger_formatter = logging.Formatter(LOG_FORMAT)
    logger_handler.setFormatter(logger_formatter)

    logger.addHandler(logger_handler)

if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    print("hint: Run with '--debug' to enable logging.")

    # Test.
    logger.debug("DEBUG")
    logger.info("INFO")
    logger.warning("WARNING")
    logger.error("ERROR")
    logger.critical("CRITICAL")
    try:
        raise RuntimeError("Test exception.")
    except RuntimeError:
        logger.exception("EXCEPTION")
        logger.warning("Warning with exception.", exc_info=True)
    logger.info("END")
