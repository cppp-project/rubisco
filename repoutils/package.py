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
Package utils.
"""

import json
from pathlib import Path
from repoutils.nls import _
from repoutils.ignorefile import load_cppp_ignore, IgnoreChecker
from repoutils.constants import REPO_PROFILE, DEFAULT_CHARSET
from repoutils.variable import AutoFormatDict
from repoutils.log import logger
from repoutils.output import output


class Package: # pylint: disable=too-many-instance-attributes
    """Package type."""

    profile: AutoFormatDict
    name: str
    version: str
    ign_checker: IgnoreChecker
    desc: str
    authors: list[str]
    webpage: str
    license: str
    subpackages: list["Package"]

    def __init__(self, profile_path: Path = REPO_PROFILE):
        """Initialize package object.

        Args:
            profile_path (Path): Profile file path.
        """

        with open(profile_path, "r", encoding=DEFAULT_CHARSET) as file:
            self.profile = json.load(file)
            self.profile = AutoFormatDict.from_dict(self.profile)

        try:
            self.name = self.profile["name"]
            self.version = self.profile["version"]
            self.ign_checker = load_cppp_ignore()
            self.desc = self.profile["description"]
            self.authors = self.profile["authors"]
            self.webpage = self.profile["webpage"]
            self.license = self.profile["license"]
            self.__subpackages = self.profile["subpackages"]
        except KeyError as exc:
            logger.fatal("Cannot load profile '%s': Key '%s' required.")
            output(
                _("Cannot load profile '{path}': Key '{key}' required."),
                fmt={"path", str(profile_path), "key", str(exc)},
                color="red"
            )

    def _load_subpkgs():
        