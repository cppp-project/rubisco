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

"""RuBP metadata generator."""

from dataclasses import dataclass
from pathlib import Path
from typing import cast

from pygit2 import GitError  # pylint: disable=E0611
from pygit2.repository import Repository
from rubisco.shared.api.kernel import Maintainer, RUConfiguration

from rubp_build.deps import generate_dependencies
from rubp_build.logger import logger
from rubp_build.version import VersionMetadata, load_versions

__all__ = ["RUBPMatadata"]


@dataclass
class RUBPMatadata:  # pylint: disable=R0902
    """RuBP metadata."""

    name: str
    version: str  # Current version.
    description: str
    maintainers: list[Maintainer]
    versions: list[VersionMetadata]
    license: str
    homepage: str | None
    tags: list[str]
    deps: list[dict[str, str]]
    latest_release: str | None

    @staticmethod
    def open_repo(path: Path) -> Repository | None:
        """Open repository."""
        try:
            return Repository(str(path))
        except (OSError, GitError):
            return None

    @classmethod
    def from_json(cls, json: RUConfiguration) -> "RUBPMatadata":
        """Create RUBPMatadata from json."""
        logger.info("Loading metadata from %s", json.path)
        deps = json.get("deps", default=[], valtype=list[str | dict[str, str]])
        # Canonicalize deps.
        deps = [
            cast("dict[str, str]", d) if isinstance(d, dict) else {"name": d}
            for d in deps
        ]
        deps.extend(generate_dependencies(json))
        maintainers = list(
            json.get(
                "maintainers",
                default=[],
                valtype=list[str] | list[dict[str, str]],
            ),
        )
        maintainer = json.get("maintainer", default=None, valtype=str | None)
        if maintainer:
            maintainers.append(maintainer)

        return cls(
            name=json.get("name", valtype=str),
            version=json.get("version", valtype=str),
            description=json.get("description", valtype=str),
            maintainers=[Maintainer.parse(m) for m in maintainers],
            versions=load_versions(json, cls.open_repo(json.path.parent)),
            license=json.get("license", valtype=str),
            homepage=json.get("homepage", valtype=str),
            tags=json.get("tags", default=[], valtype=list[str]),
            deps=deps,
            latest_release=json.get("latest-release", valtype=str),
        )

    def to_dict(self) -> dict[str, object]:
        """Convert to dict."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "maintainers": [m.to_dict() for m in self.maintainers],
            "versions": [v.to_dict() for v in self.versions],
            "license": self.license,
            "homepage": self.homepage,
            "tags": self.tags,
            "deps": self.deps,
            "latest-release": self.latest_release,
        }
