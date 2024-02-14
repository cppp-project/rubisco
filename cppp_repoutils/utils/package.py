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
from enum import Enum
from cppp_repoutils.utils.gitclone import clone
from cppp_repoutils.utils.nls import _
from cppp_repoutils.constants import REPO_PROFILE, DEFAULT_CHARSET
from cppp_repoutils.utils.variable import AutoFormatDict
from cppp_repoutils.utils.log import logger
from cppp_repoutils.utils.output import output_step


class SubpackageTypes(Enum):
    """Subpackage types."""

    KEY_NAME = "name"
    KEY_PATH = "path"
    KEY_REMOTE_TYPE = "remote-type"
    KEY_REMOTE_URL = "remote-url"
    KEY_GIT_BRANCH = "git-branch"


class Subpackage:
    """Subpackage type."""

    name: str
    path: Path
    remote_url: str
    git_branch: str

    def __init__(self, config: dict) -> None:
        """Initialize subpackage object.

        Args:
            config (dict): Subpackage config.
        """

        self.name = config[SubpackageTypes.KEY_NAME]
        self.path = Path(config[SubpackageTypes.KEY_PATH])
        self.remote_type = config[SubpackageTypes.KEY_REMOTE_TYPE]
        self.remote_url = config[SubpackageTypes.KEY_REMOTE_URL]

        self.git_branch = config[SubpackageTypes.KEY_GIT_BRANCH]

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self) -> str:
        return f"Subpackage({self.name})"

    def __eq__(self, other: "Subpackage") -> bool:
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def setup(self) -> "Package":
        """Setup subpackage."""

        clone(self.remote_url, self.path, self.git_branch)
        pkg = Package(self.path / REPO_PROFILE)
        return pkg


class Package:  # pylint: disable=too-many-instance-attributes
    """Package type."""

    profile: AutoFormatDict
    name: str
    version: str
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
            self.desc = self.profile["description"]
            self.authors = self.profile["authors"]
            self.webpage = self.profile["webpage"]
            self.license = self.profile["license"]
            self.__subpackages = self.profile["subpackages"]
        except KeyError as exc:
            logger.fatal("Cannot load profile '%s': Key '%s' required.")
            raise KeyError(exc.args[0], str(profile_path)) from exc

    def _load_subpkgs(self):
        pass
