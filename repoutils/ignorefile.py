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
Ignore file utils.
"""

from typing import Callable
import gitignore_parser

from repoutils.log import logger
from repoutils.constants import DIST_IGNORE_FILE

__all__ = ["load_cppp_ignore"]

# Ignore file checker.
IgnoreChecker = Callable


def load_cppp_ignore() -> IgnoreChecker:
    """Load cppp-repoutils ignore file.

    Returns:
        IgnoreChecker: Ignore checker.
    """

    logger.info("Loading ignore file '%s'", DIST_IGNORE_FILE)
    return gitignore_parser.parse_gitignore(DIST_IGNORE_FILE)
