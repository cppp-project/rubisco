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

"""Rubisco dependency generator for Python project."""

import tomllib
from typing import Any, cast

from packaging.requirements import Requirement
from rubisco.config import APP_NAME, DEFAULT_CHARSET
from rubisco.shared.api.exception import RUTypeError
from rubisco.shared.api.kernel import RUConfiguration
from rubisco.shared.api.l10n import _

from rubp_build.deps.interface import IDependencyGenerator

__all__ = ["PyProjectDependencyGenerator"]


class PyProjectDependencyGenerator(IDependencyGenerator):
    """Python project dependency generator."""

    config: list[str] | dict[str, Any] | None
    skip: bool

    def __init__(self, config: RUConfiguration) -> None:
        """Initialize the dependency generator.

        Args:
            config (RUConfiguration): Project config file.

        """
        config_file_path = config.path.parent / "pyproject.toml"
        requirements_file_path = config.path.parent / "requirements.txt"
        self.skip = False
        if config_file_path.is_file():
            with config_file_path.open("rb") as f:
                self.config = tomllib.load(f)
        elif requirements_file_path.is_file():
            with requirements_file_path.open(encoding=DEFAULT_CHARSET) as f:
                requirements: list[str] = []
                for line_ in f:
                    line = line_.strip()
                    if not line or line.startswith("#"):
                        continue
                    requirements.append(line)
                self.config = requirements
        else:
            self.config = None
            self.skip = True

    def need_generate(self) -> bool:
        """Check if we need to generate dependencies by this generator.

        Returns:
            bool: True if we need to generate dependencies by this generator,
                False otherwise.

        """
        return not self.skip

    def generate(self) -> list[dict[str, str]]:
        """Generate the dependency file.

        Returns:
            list[dict[str, str]]: Dependency file content.

        """
        if not self.config:
            msg = (
                "config is None but PyProjectDependencyGenerator.generate()"
                " called. This should never happen."
            )
            raise ValueError(msg)
        res: list[dict[str, str]] = []
        if isinstance(self.config, list):
            for line in self.config:
                r: dict[str, str] = {}
                req = Requirement(line)
                if req.name == APP_NAME:
                    continue
                url = req.url or f"https://pypi.org/project/{req.name}"
                r["name"] = (
                    f"{req.name}[{','.join(req.extras)}]"
                    if req.extras
                    else req.name  # "<name>[<extra>]"
                )
                r["url"] = url
                r["marker"] = str(req.marker) if req.marker else ""
                r["version"] = str(req.specifier) if req.specifier else ""
                res.append(r)
        else:
            project = self.config.get("project")
            if not isinstance(project, dict):
                raise RUTypeError(_("pyproject 'project' must be a dict."))
            for line in cast("dict[str, Any]", project).get("dependencies", []):
                r: dict[str, str] = {}
                req = Requirement(line)
                if req.name == APP_NAME:
                    continue
                url = req.url or f"https://pypi.org/project/{req.name}"
                r["name"] = (
                    f"{req.name}[{','.join(req.extras)}]"
                    if req.extras
                    else req.name  # "<name>[<extra>]"
                )
                r["url"] = url
                r["marker"] = str(req.marker) if req.marker else ""
                r["version"] = str(req.specifier) if req.specifier else ""
                res.append(r)
        return res
