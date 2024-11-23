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

"""Exetension env database."""

import re
import sqlite3
from types import TracebackType
from typing import NoReturn

from rubisco.envutils.packages import ExtensionPackageInfo
from rubisco.lib.exceptions import RUError, RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.pathlib import Path
from rubisco.lib.sqlite_strerror import sqlite_strerror
from rubisco.lib.variable import format_str
from rubisco.lib.version import Version


def _regexp(pattern: str, item: str) -> bool:  # REGEX support for SQLite3.
    # Why is this not a built-in function?
    return re.fullmatch(pattern, item) is not None


_ADD_PACKAGE_SQL = """
INSERT INTO
    extensions (
        name,
        version,
        description,
        homepage,
        maintainers,
        license,
        tags,
        requirements
    )
VALUES
    (?, ?, ?, ?, ?, ?, ?, ?)
"""


class RUEnvDB:
    """Database for extension environment."""

    db: sqlite3.Connection | None
    __path: Path

    def __init__(self, path: Path) -> None:
        """Initialize the database.

        Args:
            path (Path): The path to the database.

        """
        self.__path = path
        self.db = None

    def __enter__(self) -> "RUEnvDB":
        """Enter the context manager.

        Returns:
            RUEnvDB: The database.

        """
        if self.db is None:
            try:
                self.db = sqlite3.connect(self.__path)
                self.db.create_function("REGEXP", 2, _regexp)
            except sqlite3.OperationalError as exc:
                self._rethrow_sqlite_error(exc)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Exit the context manager.

        Args:
            exc_type (type): The exception type.
            exc_value (Exception): The exception value.
            traceback (traceback): The traceback.

        """
        if self.db is None:
            return
        self.db.close()
        self.db = None

    def __del__(self) -> None:
        """Delete the database."""
        if self.db is not None:
            self.db.close()

    def _sqlite_errmsg(self, exc: sqlite3.Error) -> str:
        return format_str(
            _("[SQLite3 Errorcode ${{codename}}(${{code}})]: ${{msg}}"),
            fmt={
                "codename": exc.sqlite_errorname,
                "code": str(exc.sqlite_errorcode),
                "msg": sqlite_strerror(exc.sqlite_errorcode),
            },
        )

    def _rethrow_sqlite_error(self, exc: sqlite3.Error) -> NoReturn:
        logger.info("Rethrowing SQLite3 error.")
        raise RUError(
            format_str(
                _(
                    "Failed to open or operate on database '[underline]"
                    "${{path}}[/underline]': ${{exc}}",
                ),
                fmt={
                    "path": str(self.__path),
                    "exc": self._sqlite_errmsg(exc),
                },
            ),
        ) from exc

    def add_packages(self, packages: list[ExtensionPackageInfo]) -> None:
        """Add a package to the database.

        Args:
            packages (list[ExtensionPackageInfo]): Packages.

        """
        with self:
            try:
                for package in packages:
                    self.db.execute(  # type: ignore[union-attr]
                        _ADD_PACKAGE_SQL,
                        (
                            package.name,
                            str(package.version),
                            package.description,
                            package.homepage,
                            ",".join(package.maintainers),
                            package.pkg_license,
                            ",".join(package.tags),
                            package.requirements,
                        ),
                    )
                    self.db.commit()  # type: ignore[union-attr]
            except sqlite3.Error as exc:
                self._rethrow_sqlite_error(exc)

    def remove_packages(self, packages: list[ExtensionPackageInfo]) -> None:
        """Remove a packages from the database.

        Args:
            packages (list[ExtensionPackageInfo]): Packages.

        """
        with self:
            try:
                for package in packages:
                    self.db.execute(  # type: ignore[union-attr]
                        "DELETE FROM extensions WHERE name = ?",
                        (package.name,),
                    )
                    self.db.commit()  # type: ignore[union-attr]
            except sqlite3.Error as exc:
                self._rethrow_sqlite_error(exc)

    def rollback(self) -> None:
        """Rollback the database."""
        with self:
            try:
                self.db.rollback()  # type: ignore[union-attr]
            except sqlite3.Error as exc:
                self._rethrow_sqlite_error(exc)

    def get_package(self, name: str) -> ExtensionPackageInfo:
        """Get a package from the database.

        Args:
            name (str): The package name.

        Returns:
            ExtensionPackageInfo: The package info.

        """
        with self:
            try:
                cursor = self.db.execute(  # type: ignore[union-attr]
                    "SELECT * FROM extensions WHERE name = ?",
                    (name,),
                )
                row = cursor.fetchone()

                return ExtensionPackageInfo(
                    name=row[0],
                    version=row[1],
                    description=row[2],
                    homepage=row[3],
                    maintainers=row[4].split(","),
                    pkg_license=row[5],
                    tags=row[6].split(","),
                    requirements=row[7],
                )
            except sqlite3.Error as exc:
                self._rethrow_sqlite_error(exc)

    def get_all_packages(self) -> list[ExtensionPackageInfo]:
        """Get all packages from the database.

        Returns:
            list[ExtensionPackageInfo]: The package infos.

        """
        with self:
            try:
                cursor = self.db.execute(  # type: ignore[union-attr]
                    "SELECT * FROM extensions",
                )

                return [
                    ExtensionPackageInfo(
                        name=row[0],
                        version=row[1],
                        description=row[2],
                        homepage=row[3],
                        maintainers=row[4].split(","),
                        pkg_license=row[5],
                        tags=row[6].split(","),
                        requirements=row[7],
                    )
                    for row in cursor.fetchall()
                ]
            except sqlite3.Error as exc:
                self._rethrow_sqlite_error(exc)

    def query_packages(self, pattern: str) -> set[ExtensionPackageInfo]:
        """Query packages from the database.

        Args:
            pattern (str): The regex pattern.

        Returns:
            list[ExtensionPackageInfo]: The package infos.

        """
        with self:
            try:
                # Check if the pattern is valid.
                try:
                    re.compile(pattern)
                except re.error as exc:
                    raise RUValueError(
                        format_str(
                            _("Invalid regex pattern: '${{pattern}}'."),
                            fmt={"pattern": pattern},
                        ),
                    ) from exc
                cursor = self.db.cursor().execute(  # type: ignore[union-attr]
                    "SELECT * FROM extensions WHERE name REGEXP ?",
                    (pattern,),
                )

                return {
                        ExtensionPackageInfo(
                            name=row[0],
                            version=Version(row[1]),
                            description=row[2],
                            homepage=row[3],
                            maintainers=row[4].split(","),
                            pkg_license=row[5],
                            tags=row[6].split(","),
                            requirements=row[7],
                        )
                        for row in cursor.fetchall()
                }
            except sqlite3.Error as exc:
                self._rethrow_sqlite_error(exc)
