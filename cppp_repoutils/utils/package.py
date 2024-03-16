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
from cppp_repoutils.utils.output import (
    output_step,
    output_warning,
    output_error,
    output,
)
from cppp_repoutils.utils.fileutil import (
    TemporaryObject,
    assert_rel_path,
    rm_recursive,
)
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
    PACKAGE_KEY_HOMEPAGE,
    PACKAGE_KEY_LICENSE,
    PACKAGE_KEY_SUBPKGS,
    PACKAGE_KEY_TAGS,
    SETUP_TEMP_CACHE,
)


def assert_is_cppp_package(path: Path):
    """Raise error if the path is not a cppp package.

    Args:
        path (Path): The path to check.

    Raises:
        AssertionError: If the path is not a cppp package.

    """

    if not (path / REPO_PROFILE).exists():
        raise AssertionError(
            _("'{path}' is not a cppp package.").format(path=path),
        )


class PackageLoaderCache:
    """
    This class is only used like a namespace to store functions that manage
    temp cache when setup packages.
    """

    cache: dict[str, dict[str, str | bool]] = {"setup": {}}

    @staticmethod
    def update_cache() -> None:
        """
        Sync cache to file. If the cache file does not exist, create it.
        Call this function when the cache is updated.
        """

        try:
            SETUP_TEMP_CACHE.touch(mode=0o666, exist_ok=True)
            with open(SETUP_TEMP_CACHE, "w", encoding=DEFAULT_CHARSET) as file:
                json.dump(PackageLoaderCache.cache, file)
            logger.info("Cache updated.")
        except KeyboardInterrupt:
            # Avoid user interrupting the writing process.
            PackageLoaderCache.update_cache()
        except OSError:
            output_warning(
                _("Cannot write cache to file '{underline}{path}{reset}'."),
                fmt={"path": str(SETUP_TEMP_CACHE)},
            )

    @staticmethod
    def load_cache() -> None:
        """
        Load cache from file. If the cache file does not exist, create it.
        Call this function when the cache is loaded.
        """

        try:
            if SETUP_TEMP_CACHE.exists():
                with open(
                    SETUP_TEMP_CACHE, "r", encoding=DEFAULT_CHARSET
                ) as file:  # noqa: E501
                    PackageLoaderCache.cache = json.load(file)
        except KeyboardInterrupt:
            PackageLoaderCache.load_cache()
        except OSError:
            output_warning(
                _("Cannot load cache from file '{underline}{path}{reset}'."),
                fmt={"path": str(SETUP_TEMP_CACHE)},
            )

    @staticmethod
    def clear_cache() -> None:
        """
        Clear cache and remove cache file.
        """

        PackageLoaderCache.cache = {"setup": {}}
        SETUP_TEMP_CACHE.unlink(missing_ok=True)

    @staticmethod
    def register_init_failed(name: str) -> None:
        """
        Register the package that failed to initialize.

        Args:
            name (str): Package name.
        """

        PackageLoaderCache.cache["setup"][name] = True
        PackageLoaderCache.update_cache()
        logger.debug("Registered package '%s' as failed to initialize.", name)

    @staticmethod
    def unregister_init_failed(name: str) -> None:
        """
        Unregister the package that failed to initialize.

        Args:
            name (str): Package name.
        """

        if name in PackageLoaderCache.cache["setup"]:
            del PackageLoaderCache.cache["setup"][name]
            PackageLoaderCache.update_cache()
            logger.debug(
                "Unregistered package '%s' as failed to initialize.",
                name,
            )

    @staticmethod
    def is_init_failed(name: str) -> bool:
        """
        Check if the package failed to initialize.

        Args:
            name (str): Package name.

        Returns:
            bool: True if the package failed to initialize, otherwise False.
        """

        return bool(PackageLoaderCache.cache["setup"].get(name, False))


SETUPSTAT_NOTSETUP = 0
SETUPSTAT_SUCCESS = 1
SETUPSTAT_FAILED = 2


class Subpackage:
    """Subpackage type."""

    name: str
    path: Path
    pkgtype: str

    attrs: AutoFormatDict

    def __init__(self, config: AutoFormatDict, name: str, basepath: Path) -> None:  # noqa: E501
        """Initialize subpackage object.

        Args:
            config (AutoFormatDict): Subpackage config.
            name (str): Subpackge name.
            basepath (Path): Base path of the subpackage.
        """

        self.name = name
        _path = config.get(PACKAGE_KEY_PATH)  # type: ignore
        _path: list[str]
        if not isinstance(_path, list):
            _path = [_path]
        if len(_path) == 0:
            raise ValueError(
                _("List '{key}' must have at least {num} objects.").format(
                    key=PACKAGE_KEY_PATH, num=1
                )
            )
        if not isinstance(_path[0], str):
            raise ValueError(
                _(
                    "The value of key {key} needs to be {type} instead of {vtype}.",  # noqa: E501
                ).format(
                    key=repr(PACKAGE_KEY_PATH),
                    type=repr("type"),
                    vtype=repr(type(_path[0]).__name__),
                )
            )
        self.path = Path(_path[0])
        for one_path in _path:
            if not isinstance(one_path, str):
                raise ValueError(
                    _(
                        "The value of key {key} needs to be {type} instead of {vtype}",  # noqa: E501 # pylint: disable-name-too-long
                    ).format(
                        key=repr(PACKAGE_KEY_PATH),
                        type=repr("type"),
                        vtype=repr(type(one_path).__name__),
                    )
                )
            path = Path(one_path)
            assert_rel_path(path)
            if path.exists():
                self.path = path
                break
        self.path = basepath / self.path
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
        return self.name

    def __repr__(self) -> str:
        return f"Subpackage({self.path})"

    def __eq__(self, other: "Subpackage") -> bool:
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.path)

    def setup(
        self,
        recursive: bool = True,
        shallow: bool = False,
        can_skip: bool = True,
    ) -> bool:
        """Setup subpackages.

        Args:
            recursive (bool, optional): Setup subpackages recursively. Defaults
                to True.
            shallow (bool, optional): Only for git subpackages. Whether to
                perform a shallow clone. Default is True.
            can_skip (bool, optional): Whether to skip the setup process if the
                subpackage has been initialized. Default is True.

        Returns:
            bool: True if the subpackage skipped, otherwise False.
        """

        logger.info("Setting up subpackage '%s'...", self.name)

        if can_skip and self.path.exists():
            output_step(
                _(
                    "Subpackage '{name}' already exists at "
                    "'{underline}{path}{reset}'."
                ),
                fmt={"name": self.name, "path": str(self.path)},
            )
            logger.info(
                "Subpackage '%s' is already exists at '%s'",
                self.name,
                self.path,
            )
            return True
        output_step(
            _(
                "Setting up subpackage '{name}' to '{underline}{path}{reset}'..."  # noqa: E501
            ),
            fmt={"name": self.name, "path": str(self.path)},
        )

        if not can_skip and self.path.exists():
            logger.info("Removing old subpackage '%s'...", self.name)
            output_step(
                _(
                    "Removing old subpackage '{name}' "
                    "('{underline}{path}{reset}') ..."
                ),
                fmt={"name": self.name, "path": str(self.path)},
            )
            rm_recursive(self.path)

        if self.pkgtype == PACKAGE_TYPE_GIT:
            clone(
                self.attrs[PACKAGE_KEY_REMOTE_URL],
                self.path,
                branch=self.attrs[PACKAGE_KEY_GIT_BRANCH],
                shallow=shallow,
            )
        elif self.pkgtype == PACKAGE_TYPE_ARCHIVE:
            with TemporaryObject.new_file() as tmpfile:
                wget(self.attrs[PACKAGE_KEY_REMOTE_URL], tmpfile.path)
                extract(
                    tmpfile.path,
                    self.path,
                    self.attrs[PACKAGE_KEY_ARCHIVE_TYPE],
                )
        elif self.pkgtype == PACKAGE_TYPE_VIRTUAL:
            # TODO: Implement virtual subpackage.
            raise NotImplementedError("Virtual subpkg is not implemented yet.")

        if recursive:
            pkgobj = self.get_package()
            if pkgobj:
                pkgobj.setup_subpkgs(True, shallow)

        logger.info("Subpackage '%s' setup finished.", self.name)
        return False

    def get_package(self) -> Union["Package", None]:
        """Get package object from subpackage.

        Returns:
            Union[Package, None]: Package object. If the subpackage is not a
                cppp package, return None.
        """

        subpkg_profile = self.path / REPO_PROFILE
        if subpkg_profile.exists():
            return Package(subpkg_profile)
        return None

    def setup_stat(self) -> int:
        """Return the setup status of the subpackage.

        Returns:
            int: Setup status.
        """

        stat = SETUPSTAT_NOTSETUP
        if self.path.exists():
            stat = SETUPSTAT_SUCCESS
        else:
            return stat
        PackageLoaderCache.load_cache()
        if PackageLoaderCache.is_init_failed(self.name):
            stat = SETUPSTAT_FAILED

        return stat


class Package:  # pylint: disable=too-many-instance-attributes
    """Package type."""

    profile: AutoFormatDict
    name: str
    version: str
    desc: str
    authors: list[str]
    homepage: str
    license: str
    tags: list[str]
    subpackages: list[Subpackage]
    __subpkgs: AutoFormatDict

    def __init__(self, profile_path: Path = REPO_PROFILE) -> None:
        """Initialize package object.

        Args:
            profile_path (Path): Profile file path.
        """

        assert_is_cppp_package(profile_path.parent)

        with open(profile_path, "r", encoding=DEFAULT_CHARSET) as file:
            self.profile = json.load(file)
            self.profile = AutoFormatDict.from_dict(self.profile)

        try:
            self.name = self.profile.get(
                PACKAGE_KEY_NAME,
                profile_path.stem,
                valtype=str,
            )
            self.version = self.profile.get(PACKAGE_KEY_VERSION, valtype=str)
            self.desc = self.profile.get(PACKAGE_KEY_DESC, "", valtype=str)
            self.authors = self.profile.get(  # type: ignore
                PACKAGE_KEY_AUTHORS, [], valtype=list
            )  # noqa: E501
            self.homepage = self.profile.get(
                PACKAGE_KEY_HOMEPAGE,
                "",
                valtype=str,
            )
            self.license = self.profile.get(
                PACKAGE_KEY_LICENSE,
                _("Unknown"),
                valtype=str,
            )
            self.tags = self.profile.get(PACKAGE_KEY_TAGS, [], valtype=list)
            self.__subpkgs = AutoFormatDict.from_dict(
                self.profile.get(
                    PACKAGE_KEY_SUBPKGS,
                    {},
                    valtype=dict,
                )
            )
            self.subpackages = []
            for name, subpkg in self.__subpkgs.items():
                subpkg = Subpackage(subpkg, name, profile_path.parent)
                self.subpackages.append(subpkg)

            logger.info("Loaded package '%s'.", profile_path)
        except KeyError as exc:
            logger.fatal("Cannot load profile '%s': Key '%s' required.")
            raise KeyError(exc.args[0], profile_path) from exc

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Package({self.name})"

    def __eq__(self, other: "Package") -> bool:
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

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

        suc_count = 0
        err_count = 0
        ign_count = 0
        PackageLoaderCache.load_cache()
        for subpkg in self.subpackages:
            try:
                try:
                    can_skip = not PackageLoaderCache.is_init_failed(
                        subpkg.name,
                    )
                    if subpkg.setup(recursive, shallow, can_skip):
                        ign_count += 1
                    else:
                        suc_count += 1
                    PackageLoaderCache.unregister_init_failed(
                        subpkg.name,
                    )
                except:  # noqa: E722
                    logger.exception(
                        "Failed to initialize subpackage '%s'.",
                        subpkg.name,
                    )
                    PackageLoaderCache.register_init_failed(subpkg.name)
                    err_count += 1
                    raise
            except KeyboardInterrupt:
                output_error(
                    _(
                        "Submodule '{underline}{name}{reset}{red}' setup "
                        "interrupted."
                    ),
                    fmt={"name": subpkg.name},
                )
        output(_("Subpackages setup finished:"), end=" ")
        output(
            _("{count} succeeded,"),
            fmt={"count": str(suc_count)},
            end=" ",
            color="green" if suc_count else "",
        )
        output(
            _("{count} ignored,"),
            fmt={"count": str(ign_count)},
            end=" ",
            color="green" if ign_count else "",
        )
        output(
            _("{count} failed."),
            fmt={"count": str(err_count)},
            color="red" if err_count else "",
        )
        if not err_count:  # Only remove cache when all subpackages are set up.
            PackageLoaderCache.clear_cache()

    def deinit_subpkgs(self) -> None:
        """Deinitialize subpackages."""

        suc_count = 0
        err_count = 0
        ign_count = 0

        for subpkg in self.subpackages:
            try:
                if subpkg.path.exists():
                    output_step(
                        _(
                            "Removing subpackage '{name}' "
                            "('{underline}{path}{reset}') ..."
                        ),
                        fmt={"name": subpkg.name, "path": str(subpkg.path)},
                    )
                    rm_recursive(subpkg.path)
                    logger.info(
                        "Removed subpackage '%s' ('%s').",
                        subpkg.name,
                        subpkg.path,
                    )
                    suc_count += 1
                else:
                    output_step(
                        _(
                            "Subpackage '{name}' "
                            "('{underline}{path}{reset}') "
                            "does not exist. Ignored."
                        ),
                        fmt={"name": subpkg.name, "path": str(subpkg.path)},
                    )
                    logger.info(
                        "Subpackage '%s' ('%s') does not exist. Ignored.",
                        subpkg.name,
                        subpkg.path,
                    )
                    ign_count += 1
            except KeyboardInterrupt:
                err_count += 1
                output_error(
                    _(
                        "Submodule '{underline}{name}{reset}{red}' removal "
                        "interrupted."
                    ),
                    fmt={"name": subpkg.name},
                )
                logger.error(
                    "Submodule '%s' removal interrupted.",
                    subpkg.name,
                )
            except OSError:
                err_count += 1
                output_error(
                    _(
                        "Failed to remove submodule '{underline}{name}{reset}{red}'."  # noqa: E501
                    ),
                    fmt={"name": subpkg.name},
                )
                logger.error(
                    "Failed to remove submodule '%s'.",
                    subpkg.name,
                )
        self.subpackages = []
        output(_("Subpackages deinitialization finished:"), end=" ")
        output(
            _("{count} succeeded,"),
            fmt={"count": str(suc_count)},
            end=" ",
            color="green" if suc_count else "",
        )
        output(
            _("{count} ignored,"),
            fmt={"count": str(ign_count)},
            end=" ",
            color="green" if ign_count else "",
        )
        output(
            _("{count} failed."),
            fmt={"count": str(err_count)},
            color="red" if err_count else "",
        )


if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    test_pkg = Package()
    test_pkg.setup_subpkgs()
    print(repr(test_pkg))
