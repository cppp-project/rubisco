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

from rubisco.envutils.env import RUEnvironment
from rubisco.envutils.packages import ExtensionPackageInfo
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.variable import format_str


def _regexp(pattern: str, item: str) -> bool:  # REGEX support for SQLite3.
    # Why is this not a built-in function?
    return re.fullmatch(pattern, item) is not None


class RUEnvDB:
    """Database for extension environment."""

    db: sqlite3.Connection
    env: RUEnvironment

    def __init__(self, env: RUEnvironment) -> None:
        """Initialize the database.

        Args:
            env (RUEnvironment): The environment.

        """
        self.env = env
        with env:
            self.db = sqlite3.connect(env.db_file)
            self.db.create_function("REGEXP", 2, _regexp)

    def add_packages(self, packages: list[ExtensionPackageInfo]) -> None:
        """Add a package to the database.

        Args:
            packages (list[ExtensionPackageInfo]): Packages.

        """
        with self.env:
            for package in packages:
                self.db.execute(
                    """
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
                    """,
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

    def remove_packages(self, packages: list[ExtensionPackageInfo]) -> None:
        """Remove a packages from the database.

        Args:
            packages (list[ExtensionPackageInfo]): Packages.

        """
        with self.env:
            for package in packages:
                self.db.execute(
                    "DELETE FROM extensions WHERE name = ?",
                    (package.name,),
                )

    def get_package(self, name: str) -> ExtensionPackageInfo:
        """Get a package from the database.

        Args:
            name (str): The package name.

        Returns:
            ExtensionPackageInfo: The package info.

        """
        with self.env:
            cursor = self.db.execute(
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

    def get_all_packages(self) -> list[ExtensionPackageInfo]:
        """Get all packages from the database.

        Returns:
            list[ExtensionPackageInfo]: The package infos.

        """
        with self.env:
            cursor = self.db.execute("SELECT * FROM extensions")

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

    def query_packages(self, pattern: str) -> list[ExtensionPackageInfo]:
        """Query packages from the database.

        Args:
            pattern (str): The regex pattern.

        Returns:
            list[ExtensionPackageInfo]: The package infos.

        """
        with self.env:
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
            cursor = self.db.cursor().execute(
                "SELECT * FROM extensions WHERE name REGEXP ?",
                (pattern,),
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
