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

"""Project configuration loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from beartype import beartype

from rubisco.config import APP_VERSION, USER_REPO_CONFIG
from rubisco.kernel.config_loader import RUConfiguration
from rubisco.kernel.project_config.hook import ProjectHook
from rubisco.kernel.project_config.maintainer import Maintainer
from rubisco.lib.exceptions import (
    RUNotRubiscoProjectError,
    RUValueError,
)
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.variable import (
    AutoFormatDict,
    assert_iter_types,
    make_pretty,
    pop_variables,
    push_variables,
)
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.version import Version

__all__ = [
    "ProjectConfigration",
    "load_project_config",
]


class ProjectConfigration:  # pylint: disable=too-many-instance-attributes
    """Project configuration instance."""

    config: RUConfiguration

    # Project mandatory configurations.
    name: str
    version: Version

    # Project optional configurations.
    description: str
    rubisco_min_version: Version
    maintainers: list[Maintainer] | Maintainer
    license: str | None
    hooks: AutoFormatDict

    pushed_variables: list[str]

    def __init__(self, config_file: Path) -> None:
        """Initialize the project configuration."""
        self.config = RUConfiguration(config_file, AutoFormatDict())
        self.hooks = AutoFormatDict()
        self.pushed_variables = []

        self._load()

    def _check_version(self) -> None:
        if self.rubisco_min_version > APP_VERSION:
            raise RUValueError(
                fast_format_str(
                    _(
                        "The minimum version of rubisco required by the "
                        "project [underline][link=${{uri}}]${{name}}[/link]"
                        "[/underline]' is "
                        "'[cyan]${{version}}[/cyan]'.",
                    ),
                    fmt={
                        "uri": self.config.path.as_uri(),
                        "name": make_pretty(self.name, _("<Unnamed>")),
                        "version": str(self.rubisco_min_version),
                    },
                ),
                hint=_("Please upgrade rubisco to the required version."),
            )

    def _load(self) -> None:
        if not self.config.path.is_file():
            logger.warning(
                "The project configuration file '%s' is not found.",
                self.config.path,
            )
            raise RUNotRubiscoProjectError(
                fast_format_str(
                    _("Project configuration file '${{path}}' is not found."),
                    fmt={
                        "path": make_pretty(self.config.path),
                    },
                ),
            )
        self.config = RUConfiguration.load_from_file(self.config.path)

        self.name = self.config.get("name", valtype=str)
        self.version = Version(self.config.get("version", valtype=str))
        self.description = self.config.get(
            "description",
            "",
            valtype=str,
        )

        self.rubisco_min_version = Version(
            self.config.get("rubisco-min-version", "0.0.0", valtype=str),
        )

        self._check_version()

        _m = self.config.get(
            "maintainer",
            default=None,
            valtype=str | None,
        )
        if _m:
            maintainer = Maintainer.parse(_m)
            self.maintainers = [maintainer]
        else:
            self.maintainers = []

        _m = self.config.get(
            "maintainers",
            default=None,
            valtype=list | dict[str, str] | None,
        )
        if _m:
            self.maintainers.extend([Maintainer.parse(x) for x in _m])

        self.license = self.config.get(
            "license",
            None,
            valtype=str,
        )

        hooks: AutoFormatDict = self.config.get(
            "hooks",
            {},
            valtype=dict,
        )
        assert_iter_types(
            hooks.values(),
            dict,
            RUValueError(
                _("Hooks must be a dictionary."),
            ),
        )
        for name, data in hooks.items():
            self.hooks[name] = ProjectHook(
                data,  # type: ignore[assignment]
                name,
            )

        # Serialize configuration to variables.
        def _push_vars(
            obj: AutoFormatDict | list[Any] | Any,  # noqa: ANN401
            prefix: str,
        ) -> None:
            if isinstance(obj, AutoFormatDict):
                for key, value in obj.items():
                    _push_vars(value, f"{prefix}.{key}")
            elif isinstance(obj, list):
                self.pushed_variables.append(f"{prefix}.length")
                push_variables(f"{prefix}.length", len(obj))  # type: ignore[arg-type]
                for idx, val in enumerate(obj):  # type: ignore[arg-type]
                    _push_vars(val, f"{prefix}.{idx}")
            else:
                self.pushed_variables.append(prefix)
                push_variables(prefix, obj)

        _push_vars(self.config, "project")

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

    def run_hook(self, name: str) -> None:
        """Run a hook by its name.

        Args:
            name (str): The hook name.

        """
        cast("ProjectHook", self.hooks[name]).run()

    def __del__(self) -> None:
        """Remove all pushed variables."""
        for val in self.pushed_variables:
            pop_variables(val)


@beartype
def load_project_config(project_dir: Path) -> ProjectConfigration:
    """Load the project configuration from the given configuration file.

    Args:
        project_dir (Path): The path to the project configuration file.

    Returns:
        ProjectConfigration: The project configuration instance.

    """
    return ProjectConfigration(project_dir / USER_REPO_CONFIG)


_T = Path  # Make Ruff happy.
