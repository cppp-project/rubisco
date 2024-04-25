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
Project configuration loader.
"""

from pathlib import Path

import json5 as json

from repoutils.constants import REPO_PROFILE
from repoutils.lib.exceptions import RUValueException
from repoutils.lib.l10n import _
from repoutils.lib.path_glob import glob_path, resolve_path
from repoutils.lib.variable import AutoFormatDict, format_str
from repoutils.lib.version import Version

__all__ = [
    "ProjectConfigration",
    "load_project_config",
]


class ProjectConfigration:
    """
    Project configuration instance.
    """

    config_file: Path
    config: AutoFormatDict

    # Project mandatory configurations.
    name: str
    version: Version

    # Project optional configurations.
    description: str
    repoutils_min_version: Version

    def __init__(self, config_file: Path):
        self.config_file = config_file
        self.config = AutoFormatDict()

        self._load()

    def _load(self):
        with self.config_file.open() as file:
            self.config = AutoFormatDict.from_dict(json.load(file))

        self.name = self.config.get("name", valtype=str)
        self.version = Version(self.config.get("version", valtype=str))
        self.description = self.config.get(
            "description",
            default="",
            valtype=str,
        )

        self.repoutils_min_version = Version(
            self.config.get("repoutils-min-version", "0.0.0", valtype=str)
        )

    def __repr__(self) -> str:
        """Get the string representation of the project configuration.

        Returns:
            str: The string representation of the project configuration.
        """

        return f"<ProjectConfiguration: {self.name} {self.version}>"

    def __str__(self) -> str:
        """Get the string representation of the project configuration.

        Returns:
            str: The string representation of the project configuration.
        """

        return repr(self)


def _load_config(config_file: Path, loaded_list: list[Path]) -> AutoFormatDict:
    config_file = config_file.resolve()
    with config_file.open() as file:
        config = AutoFormatDict.from_dict(json.load(file))
        if not isinstance(config, AutoFormatDict):
            raise RUValueException(
                format_str(
                    _("Invalid configuration in '{underline}{path}{reset}'."),
                    fmt={"path": str(config_file)},
                ),
                hint=_("Configuration must be a json5 object. (dict)"),
            )
        for include in config.get("includes", [], valtype=list):
            if not isinstance(include, str):
                raise RUValueException(
                    format_str(
                        _(
                            "Invalid path in '{underline}{path}{reset}'."
                        ),
                        fmt={"path": str(config_file)},
                    )
                )
            include_file = config_file.parent / include
            if include_file.is_dir():
                include_file = include_file / REPO_PROFILE
            include_file = resolve_path(include_file)
            for one_file in glob_path(include_file):
                if one_file in loaded_list:
                    raise RUValueException(
                        format_str(
                            _(
                                "Circular includes detected in '{underline}"
                                "{path}{reset}'."
                            ),
                            fmt={"path": str(one_file)},
                        ),
                        hint=_("Remove the circular includes."),
                    )
                loaded_list.append(one_file)

            config.merge(_load_config(include_file, loaded_list))

    return config


def load_project_config(project_dir: Path) -> ProjectConfigration:
    """Load the project configuration from the given configuration file.

    Args:
        project_dir (Path): The path to the project configuration file.

    Returns:
        ProjectConfigration: The project configuration instance.
    """

    return ProjectConfigration(project_dir / REPO_PROFILE)


if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    print(_load_config(Path("project.json"), []))
