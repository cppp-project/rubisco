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
from typing import Union
from pathlib import Path
from cppp_repoutils.utils.compress import extract
from cppp_repoutils.utils.wget import wget
from cppp_repoutils.utils.gitclone import clone
from cppp_repoutils.utils.nls import _
from cppp_repoutils.utils.variable import AutoFormatDict
from cppp_repoutils.utils.log import logger
from cppp_repoutils.utils.output import output_step
from cppp_repoutils.utils.fileutil import TemporaryObject
from cppp_repoutils.constants import (
    REPO_PROFILE,
    DEFAULT_CHARSET,
    PACKAGE_TYPE_GIT,
    PACKAGE_TYPE_ARCHIVE,
    PACKAGE_TYPE_VIRTUAL,
    PACKAGE_KEY_PATH,
    PACKAGE_KEY_TYPE,
    PACKAGE_KEY_REMOTE_URL,
    PACKAGE_KEY_GIT_BRANCH,
    PACKAGE_KEY_ARCHIVE_TYPE,
    PACKAGE_KEY_NAME,
    PACKAGE_KEY_VERSION,
    PACKAGE_KEY_DESC,
    PACKAGE_KEY_AUTHORS,
    PACKAGE_KEY_WEBPAGE,
    PACKAGE_KEY_LICENSE,
    PACKAGE_KEY_SUBPKGS,
)

# TODO: Refactor.


class Subpackage:
    """Subpackage type."""

    path: Path
    pkgtype: str

    attrs: AutoFormatDict[str]

    def __init__(self, config: AutoFormatDict) -> None:
        """Initialize subpackage object.

        Args:
            config (AutoFormatDict): Subpackage config.
        """

        self.path = Path(config[PACKAGE_KEY_PATH])
        self.pkgtype = config[PACKAGE_KEY_TYPE]
        self.attrs = AutoFormatDict({})
        if self.pkgtype == PACKAGE_TYPE_GIT:
            self.attrs[PACKAGE_KEY_REMOTE_URL] = config[PACKAGE_KEY_REMOTE_URL]
            self.attrs[PACKAGE_KEY_GIT_BRANCH] = config.get(
                PACKAGE_KEY_GIT_BRANCH, None
            )
        elif self.pkgtype == PACKAGE_TYPE_ARCHIVE:
            self.attrs[PACKAGE_KEY_ARCHIVE_TYPE] = config[
                PACKAGE_KEY_ARCHIVE_TYPE
            ]  # noqa: E501
            self.attrs[PACKAGE_KEY_REMOTE_URL] = config[PACKAGE_KEY_REMOTE_URL]
        elif self.pkgtype == PACKAGE_TYPE_VIRTUAL:
            # TODO: Implement virtual subpackage.
            raise NotImplementedError("Virtual subpkg is not implemented yet.")
        else:
            raise ValueError(
                _("Invalid subpackage type: {type}").format(type=self.pkgtype)
            )

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self) -> str:
        return f"Subpackage({self.path})"

    def __eq__(self, other: "Subpackage") -> bool:
        return self.path == other.path

    def __hash__(self) -> int:
        return hash(self.path)

    def setup(
        self, recursive: bool = True, shallow: bool = False  # noqa: E501
    ) -> Union["Package", None]:
        """Setup subpackage.

        Args:
            recursive (bool, optional): Setup subpackages recursively. Defaults
                to True.
            shallow (bool, optional): Only for git subpackages. Whether to
                perform a shallow clone. Default is True.

        Returns:
            Union["Package", None]: The package object of this subpackage. If the
                subpackage is not a cppp-repo, return None.
        """

        pkgobj: Package
        subpkg_profile = self.path / REPO_PROFILE
        if self.pkgtype == PACKAGE_TYPE_GIT:
            clone(
                self.attrs[PACKAGE_KEY_REMOTE_URL],
                self.path,
                branch=self.attrs[PACKAGE_KEY_GIT_BRANCH],
                shallow=shallow,
            )
            if not subpkg_profile.exists():
                return None
            pkgobj = Package()
        elif self.pkgtype == PACKAGE_TYPE_ARCHIVE:
            with TemporaryObject.new_file() as tmpfile:
                wget(self.attrs[PACKAGE_KEY_REMOTE_URL], tmpfile.path)
                extract(
                    tmpfile.path,
                    self.path,
                    self.attrs[PACKAGE_KEY_ARCHIVE_TYPE],
                )
            if not subpkg_profile.exists():
                return None
            pkgobj = Package(self.path / REPO_PROFILE)
        elif self.pkgtype == PACKAGE_TYPE_VIRTUAL:
            # TODO: Implement virtual subpackage.
            raise NotImplementedError("Virtual subpkg is not implemented yet.")

        if recursive:
            pkgobj.setup_subpkgs(True, shallow)
        return pkgobj


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
    __subpkgs: list[AutoFormatDict]

    def __init__(self, profile_path: Path = REPO_PROFILE) -> None:
        """Initialize package object.

        Args:
            profile_path (Path): Profile file path.
        """

        with open(profile_path, "r", encoding=DEFAULT_CHARSET) as file:
            self.profile = json.load(file)
            self.profile = AutoFormatDict.from_dict(self.profile)

        try:
            self.name = self.profile[PACKAGE_KEY_NAME]
            self.version = self.profile[PACKAGE_KEY_VERSION]
            self.desc = self.profile.get(PACKAGE_KEY_DESC, "")
            self.authors = self.profile.get(
                PACKAGE_KEY_AUTHORS, [_("Anonymous")]  # noqa: E501
            )
            self.webpage = self.profile.get(PACKAGE_KEY_WEBPAGE, "")
            self.license = self.profile[PACKAGE_KEY_LICENSE]
            self.__subpkgs = self.profile.get(PACKAGE_KEY_SUBPKGS, [])
            logger.info("Loaded package '%s'.", profile_path)
        except KeyError as exc:
            logger.fatal("Cannot load profile '%s': Key '%s' required.")
            raise KeyError(exc.args[0], profile_path) from exc

    def setup_subpkgs(
        self, recursive: bool = True, shallow: bool = False  # noqa: E501
    ) -> None:
        """Setup subpackage.

        Args:
            recursive (bool, optional): Setup subpackages recursively. Defaults
                to True.
            shallow (bool, optional): Only for git subpackages. Whether to
                perform a shallow clone. Default is True.
        """

        self.subpackages = []
        for subpkg in self.__subpkgs:
            output_step(
                _("Setting up subpackage `{underline}{path}{reset}` ..."),
                fmt={"path": subpkg[PACKAGE_KEY_PATH]},
            )
            subpkg = Subpackage(subpkg)
            subpkg_object = subpkg.setup(recursive, shallow)
            self.subpackages.append(subpkg_object)


if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    test_pkg = Package()
    test_pkg.setup_subpkgs()
    print(test_pkg)
