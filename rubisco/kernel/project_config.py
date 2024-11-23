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

from typing import Any

import json5 as json

from rubisco.config import APP_VERSION, USER_REPO_CONFIG
from rubisco.kernel.workflow import run_inline_workflow, run_workflow
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.fileutil import glob_path, resolve_path
from rubisco.lib.l10n import _
from rubisco.lib.pathlib import Path
from rubisco.lib.process import Process
from rubisco.lib.variable import (
    AutoFormatDict,
    assert_iter_types,
    format_str,
    make_pretty,
    pop_variables,
    push_variables,
)
from rubisco.lib.version import Version

__all__ = [
    "ProjectConfigration",
    "ProjectHook",
    "load_project_config",
]


class ProjectHook:  # pylint: disable=too-few-public-methods
    """Project hook."""

    _raw_data: AutoFormatDict
    name: str

    def __init__(self, data: AutoFormatDict, name: str) -> None:
        """Initialize the project hook."""
        self._raw_data = data
        self.name = name

    def run(self) -> None:
        """Run this hook."""
        variables: AutoFormatDict = self._raw_data.get(
            "vars",
            {},
            valtype=dict,
        )
        try:
            for name, val in variables.items():  # Push all variables first.
                push_variables(name, val)

            cmd = self._raw_data.get("exec", None, valtype=str | list | None)
            workflow = self._raw_data.get("run", None, valtype=str | None)
            inline_wf = self._raw_data.get(
                "workflow",
                None,
                valtype=dict | AutoFormatDict | list | None,
            )

            if not cmd and not workflow and not inline_wf:
                raise RUValueError(
                    format_str(
                        _("Hook '${{name}}' is invalid."),
                        fmt={"name": make_pretty(self.name)},
                    ),
                    hint=_(
                        "A workflow [yellow]SHOULD[/yellow] contain at "
                        "least 'exec', 'run' and 'workflow'.",
                    ),
                )

            # Then, run inline workflow.
            if inline_wf:
                run_inline_workflow(inline_wf)

            # Then, run workflow.
            if workflow:
                run_workflow(Path(workflow))

            # Finally, execute shell command.
            if cmd:
                Process(cmd).run()
        finally:
            for name in variables:
                pop_variables(name)


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
    maintainer: list[str] | str
    license: str
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
        with self.config_file.open() as file:
            self.config = AutoFormatDict(json.load(file))

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
                format_str(
                    _(
                        "The minimum version of rubisco required by the "
                        "project '[underline]${{name}}[/underline]' is "
                        "'[underline]${{version}}[/underline]'.",
                    ),
                    fmt={
                        "name": make_pretty(self.name, _("<Unnamed>")),
                        "version": str(self.rubisco_min_version),
                    },
                ),
                hint=_("Please upgrade rubisco to the required version."),
            )

        self.maintainer = self.config.get(
            "maintainer",
            _("[yellow]Unknown[/yellow]"),
            valtype=list | str,
        )

        self.license = self.config.get(
            "license",
            _("[yellow]Unknown[/yellow]"),
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
            obj: AutoFormatDict | list | Any,  # noqa: ANN401
            prefix: str,
        ) -> None:
            if isinstance(obj, AutoFormatDict):
                for key, value in obj.items():
                    _push_vars(value, f"{prefix}.{key}")
            elif isinstance(obj, list):
                self.pushed_variables.append(f"{prefix}.length")
                push_variables(f"{prefix}.length", len(obj))
                for idx, val in enumerate(obj):
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
        self.hooks[name].run()

    def __del__(self) -> None:
        """Remove all pushed variables."""
        for val in self.pushed_variables:
            pop_variables(val)


def _load_config(config_file: Path, loaded_list: list[Path]) -> AutoFormatDict:
    config_file = config_file.resolve()
    with config_file.open() as file:
        config = AutoFormatDict(json.load(file))
        if not isinstance(config, AutoFormatDict):
            raise RUValueError(
                format_str(
                    _(
                        "Invalid configuration in file "
                        "'[underline]${{path}}[/underline]'.",
                    ),
                    fmt={"path": make_pretty(config_file.absolute())},
                ),
                hint=_("Configuration must be a JSON5 object. (dict)"),
            )
        for include in config.get("includes", [], valtype=list):
            if not isinstance(include, str):
                raise RUValueError(
                    format_str(
                        _(
                            "Invalid path '[underline]${{path}}[/underline]'.",
                        ),
                        fmt={"path": make_pretty(config_file.absolute())},
                    ),
                )
            include_file = config_file.parent / include
            if include_file.is_dir():
                include_file = include_file / USER_REPO_CONFIG
            include_file = resolve_path(include_file)
            for one_file in glob_path(include_file):
                if one_file in loaded_list:  # Avoid circular dependencies.
                    continue  # Skip already loaded files.
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
    return ProjectConfigration(project_dir / USER_REPO_CONFIG)


if __name__ == "__main__":
    import rich

    rich.print(_load_config(Path("project.json"), []))
