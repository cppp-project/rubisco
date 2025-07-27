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

from typing import TYPE_CHECKING, Any, cast

import json5 as json

from rubisco.config import APP_VERSION, USER_REPO_CONFIG
from rubisco.kernel.project_config.hook import ProjectHook
from rubisco.kernel.project_config.maintainer import Maintainer
from rubisco.lib.exceptions import (
    RUNotRubiscoProjectError,
    RUTypeError,
    RUValueError,
)
from rubisco.lib.fileutil import glob_path, resolve_path
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
from rubisco.lib.variable.typecheck import is_instance
from rubisco.lib.version import Version
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

if TYPE_CHECKING:
    from pathlib import Path

__all__ = [
    "ProjectConfigration",
    "load_project_config",
]


class ProjectConfigration:  # pylint: disable=too-many-instance-attributes
    """Project configuration instance."""

    config_file: Path
    config: AutoFormatDict

    # Project mandatory configurations.
    name: str
    version: Version

    # Project optional configurations.
    description: str
    rubisco_min_version: Version
    maintainer: list[Maintainer] | Maintainer
    license: str | None
    hooks: AutoFormatDict

    pushed_variables: list[str]

    def __init__(self, config_file: Path) -> None:
        """Initialize the project configuration."""
        self.config_file = config_file
        self.config = AutoFormatDict()
        self.hooks = AutoFormatDict()
        self.pushed_variables = []

        self._load()

    def _load(self) -> None:
        if not self.config_file.is_file():
            logger.warning(
                "The project configuration file '%s' is not found.",
                self.config_file,
            )
            raise RUNotRubiscoProjectError(
                fast_format_str(
                    _("Project configuration file '${{path}}' is not found."),
                    fmt={
                        "path": make_pretty(self.config_file),
                    },
                ),
            )
        self.config = _load_config(self.config_file, [])

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
                        "uri": self.config_file.as_uri(),
                        "name": make_pretty(self.name, _("<Unnamed>")),
                        "version": str(self.rubisco_min_version),
                    },
                ),
                hint=_("Please upgrade rubisco to the required version."),
            )

        self.maintainer = [
            Maintainer.parse(x)
            for x in self.config.get(
                "maintainer",
                valtype=list | str | dict[str, str],
            )
        ]

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


def _load_config(config_file: Path, loaded_list: list[Path]) -> AutoFormatDict:
    config_file = config_file.resolve()
    with config_file.open() as file:
        json_data = json.load(file)
        if not is_instance(json_data, dict[str, object]):
            raise RUTypeError(
                _("The configuration file must be a JSON5 object."),
            )
        config = AutoFormatDict(json_data)
        for include in config.get("includes", [], valtype=list):
            if not isinstance(include, str):
                raise RUValueError(
                    fast_format_str(
                        _(
                            "Invalid path ${{path}}.",
                        ),
                        fmt={"path": make_pretty(config_file.absolute())},
                    ),
                )
            include_file = config_file.parent / include
            if include_file.is_dir():
                include_file = include_file / USER_REPO_CONFIG
            include_file = resolve_path(include_file)
            loaded_list.append(config_file)
            for one_file in glob_path(include_file):
                if one_file in loaded_list:  # Avoid circular dependencies.
                    logger.warning(
                        "Circular dependency detected: %s",
                        one_file,
                    )
                    call_ktrigger(
                        IKernelTrigger.on_warning,
                        message=fast_format_str(
                            _(
                                "Circular dependency detected: ${{path}}.",
                            ),
                            fmt={
                                "path": make_pretty(one_file),
                            },
                        ),
                    )
                    continue  # Skip loaded file.
                loaded_list.append(one_file)
                config.merge(_load_config(one_file, loaded_list))

    return config


def load_project_config(project_dir: Path) -> ProjectConfigration:
    """Load the project configuration from the given configuration file.

    Args:
        project_dir (Path): The path to the project configuration file.

    Returns:
        ProjectConfigration: The project configuration instance.

    """
    return ProjectConfigration(project_dir / USER_REPO_CONFIG)
