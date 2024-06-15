# -*- coding: utf-8 -*-
# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2024 The C++ Plus Project.
# This file is part of the repoutils.
#
# repoutils is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# repoutils is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Clean log file.
"""

import datetime
import re

from repoutils.config import (DEFAULT_CHARSET, LOG_FILE, LOG_KEEP_DAYS,
                              LOG_REGEX, LOG_TIME_FORMAT)


def get_time(log_line: str) -> datetime.datetime:
    """Get the time from a log line.

    Args:
        log_line (str): The log line.

    Returns:
        datetime.datetime: The time of the log. If the time cannot be parsed,
            the current time is returned.
    """

    try:
        timestr = re.match(LOG_REGEX, log_line).groups()[0]
        return datetime.datetime.strptime(timestr, LOG_TIME_FORMAT)
    except (AttributeError, ValueError):
        return datetime.datetime(year=1945, month=8, day=15)


def _is_old_log(line: str) -> bool:
    return (datetime.datetime.now() - get_time(line)).days > LOG_KEEP_DAYS


def clean_log():
    """Clean the log file.

    The log file is cleaned by removing all log lines that are older than
    LOG_KEEP_DAYS days.

    Returns:
        int: The number of log lines that were removed.
    """

    clean_count = 0

    try:
        with open(LOG_FILE, "r", encoding=DEFAULT_CHARSET) as f:
            for line in f:
                line = line.strip()
                clean_count += 1
                if not _is_old_log(line):
                    break
        clean_count -= 1
        _clean_count = clean_count
        with open(LOG_FILE, "r+", encoding=DEFAULT_CHARSET) as f:
            for _ in range(_clean_count):
                f.readline()
            lines = f.readlines()
            f.seek(0)
            f.truncate()
            f.writelines(lines)
    except OSError:
        pass

    return clean_count


if __name__ == "__main__":
    import rich

    rich.print(f"{__file__}: {__doc__.strip()}")

    rich.print(f"[blue]=>[/blue] Cleaned {clean_log()} log lines.")
