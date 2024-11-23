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

"""C++ Plus Rubisco CLI hook utils."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rubisco.cli.main.arg_parser import hook_commands
from rubisco.config import USER_REPO_CONFIG
from rubisco.kernel.project_config import load_project_config
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.pathlib import Path
from rubisco.lib.variable import format_str, make_pretty

if TYPE_CHECKING:
    from rubisco.kernel.project_config import ProjectConfigration

__all__ = [
    "bind_hook",
    "call_hook",
    "get_hooks",
    "get_project_config",
    "load_project",
]


_hooks: dict[str, list] = {}

_project_config: ProjectConfigration | None = None


def get_hooks() -> dict[str, list]:
    """Get all hooks.

    Returns:
        dict[str, list]: The hooks.

    """
    return _hooks


def get_project_config() -> ProjectConfigration | None:
    """Get the project config.

    Returns:
        ProjectConfigration | None: The project config.

    """
    return _project_config


def bind_hook(name: str) -> None:
    """Bind hook to a command.

    Args:
        name (str): Hook name.

    """
    logger.debug("Binding hook: %s", name)
    if _project_config and name in _project_config.hooks:
        if name not in _hooks:
            _hooks[name] = []
        _hooks[name].append(_project_config.hooks[name])


def call_hook(name: str) -> None:
    """Call a hook.

    Args:
        name (str): The hook name.

    """
    if name not in _hooks:
        raise RUValueError(
            format_str(
                _("Undefined command or hook ${{name}}"),
                fmt={"name": make_pretty(name)},
            ),
            hint=_("Perhaps a typo?"),
        )
    for hook in _hooks[name]:
        hook.run()


def load_project() -> None:
    """Load the project in cwd."""
    global _project_config  # pylint: disable=global-statement # noqa: PLW0603
    try:
        _project_config = load_project_config(Path.cwd())
        for hook_name in _project_config.hooks:  # Bind all hooks.
            bind_hook(hook_name)
            hook_commands.add_parser(
                hook_name,
                help=format_str(
                    _("(${{num}} hooks)"),
                    fmt={"num": str(len(_hooks[hook_name]))},
                ),
            )
    except FileNotFoundError as exc:
        raise RUValueError(
            format_str(
                _(
                    "Working directory '[underline]${{path}}[/underline]'"
                    " not a rubisco project.",
                ),
                fmt={"path": make_pretty(Path.cwd().absolute())},
            ),
            hint=format_str(
                _("'[underline]${{path}}[/underline]' is not found."),
                fmt={"path": make_pretty(USER_REPO_CONFIG.absolute())},
            ),
        ) from exc
