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

"""Rubisco extensions interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rubisco.config import (
    GLOBAL_EXTENSIONS_VENV_DIR,
    USER_EXTENSIONS_VENV_DIR,
    WORKSPACE_EXTENSIONS_VENV_DIR,
)
from rubisco.kernel.config_file import config_file
from rubisco.kernel.workflow import Step, _set_extloader, register_step_type
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.load_module import import_module_from_path
from rubisco.lib.log import logger
from rubisco.lib.variable import format_str, make_pretty
from rubisco.shared.ktrigger import (
    IKernelTrigger,
    bind_ktrigger_interface,
    call_ktrigger,
)

if TYPE_CHECKING:
    from rubisco.lib.pathlib import Path
    from rubisco.lib.version import Version

__all__ = ["IRUExtention", "load_extension"]


class IRUExtention:
    """Rubisco extension interface."""

    name: str
    description: str
    version: Version
    ktrigger: IKernelTrigger
    workflow_steps: dict[str, type[Step]]
    steps_contributions: dict[type[Step], list[str]]

    def __init__(self) -> None:
        """Construct the instance.

        Please DO NOT initialize the extension here.
        """
        self.workflow_steps = {}
        self.steps_contributions = {}

    def extension_can_load_now(self) -> bool:
        """Check if the extension can load now.

        Some extensions may initialize
        optionally like 'CMake' or 'Rust'.

        This method MUST be implemented by the subclass.

        Raises:
            NotImplementedError: Raise if the method is not implemented.

        Returns:
            bool: True if the extension can load now, otherwise False.

        """
        raise NotImplementedError

    def on_load(self) -> None:
        """Load the extension.

        Initialize the extension here.
        This method MUST be implemented by the subclass.

        """
        raise NotImplementedError

    def reqs_is_sloved(self) -> bool:
        """Check if the system requirements are solved.

        This method should return True if the system requirements are solved,
        otherwise False.

        This method MUST be implemented by the subclass.

        Raises:
            NotImplementedError: Raise if the method is not implemented.

        Returns:
            bool: True if the system requirements are solved, otherwise False.

        """
        raise NotImplementedError

    def reqs_solve(self) -> None:
        """Solve the system requirements.

        This method MUST be implemented by the subclass.
        If the slution is not possible, please raise an exception here.
        It is recommended to use RUError if you have hint, docurl, etc.
        """
        raise NotImplementedError


invalid_ext_names = ["rubisco"]  # Avoid logger's name conflict.


# A basic extension contains these modules or variables:
#   - extension/        directory    ---- The extension directory.
#       - __init__.py   file         ---- The extension module.
#           - instance  IRUExtention ---- The extension instance
def load_extension(  # pylint: disable=too-many-branches # noqa: C901 PLR0912
    path: Path | str,
    strict: bool = False,  # noqa: FBT001 FBT002
) -> None:
    """Load the extension.

    Args:
        path (Path | str): The path of the extension or it's name.
            If the path is a name, the extension will be loaded from the
            default extension directory.
        strict (bool, optional): If True, raise an exception if the extension
            loading failed.

    """
    try:
        if isinstance(path, str):
            if (WORKSPACE_EXTENSIONS_VENV_DIR / path).is_dir():
                path = GLOBAL_EXTENSIONS_VENV_DIR / path
            elif (USER_EXTENSIONS_VENV_DIR / path).is_dir():
                path = USER_EXTENSIONS_VENV_DIR / path
            elif (GLOBAL_EXTENSIONS_VENV_DIR / path).is_dir():
                path = WORKSPACE_EXTENSIONS_VENV_DIR / path
            else:
                raise RUValueError(  # noqa: TRY301
                    format_str(
                        _(
                            "The extension '${{name}}' does not exist in"
                            " workspace, user, or global extension directory.",
                        ),
                        fmt={"name": path},
                    ),
                    hint=format_str(
                        _("Try to load the extension as a path."),
                    ),
                )

        if not path.is_dir():
            raise RUValueError(  # noqa: TRY301
                format_str(
                    _(
                        "The extension path '[underline]${{path}}[/underline]'"
                        " is not a directory.",
                    ),
                    fmt={"path": make_pretty(path.absolute())},
                ),
            )

        # Load the extension.

        try:
            module = import_module_from_path(path)
        except FileNotFoundError as exc:
            raise RUValueError(
                format_str(
                    _(
                        "The extension path '[underline]${{path}}[/underline]'"
                        " does not exist.",
                    ),
                    fmt={"path": make_pretty(path.absolute())},
                ),
            ) from exc
        except ImportError as exc:
            raise RUValueError(
                format_str(
                    _(
                        "Failed to load extension '[underline]${{path}}"
                        "[/underline]'.",
                    ),
                    fmt={"path": make_pretty(path.absolute())},
                ),
                hint=format_str(
                    _(
                        "Please make sure this extension is valid.",
                    ),
                ),
            ) from exc

        if not hasattr(module, "instance"):
            raise RUValueError(  # noqa: TRY301
                format_str(
                    _(
                        "The extension '[underline]${{path}}[/underline]' does"
                        " not have an instance.",
                    ),
                    fmt={"path": make_pretty(path.absolute())},
                ),
                hint=format_str(
                    _(
                        "Please make sure this extension is valid.",
                    ),
                ),
            )
        instance: IRUExtention = module.instance

        # Security check.
        if instance.name in invalid_ext_names:
            raise RUValueError(  # noqa: TRY301
                format_str(
                    _("Invalid extension name: '${{name}}' ."),
                    fmt={"name": instance.name},
                ),
                hint=format_str(
                    _(
                        "Please use a different name for the extension.",
                    ),
                ),
            )

        logger.info("Loading extension '%s'...", instance.name)

        # Check if the extension can load now.
        if not instance.extension_can_load_now():
            logger.info("Skipping extension '%s'...", instance.name)
            return

        # Load the extension.
        if not instance.reqs_is_sloved():
            logger.info(
                "Solving system requirements for extension '%s'...",
                instance.name,
            )
            instance.reqs_solve()
            if not instance.reqs_is_sloved():
                logger.error(
                    "Failed to solve system requirements for extension '%s'.",
                    instance.name,
                )
                return

        # Register the workflow steps.
        for step_name, step in instance.workflow_steps.items():
            contributions = []
            if step in instance.steps_contributions:
                contributions = instance.steps_contributions[step]
            register_step_type(step_name, step, contributions)

        instance.on_load()
        bind_ktrigger_interface(
            instance.name,
            instance.ktrigger,
        )
        call_ktrigger(IKernelTrigger.on_extension_loaded, instance=instance)
        logger.info("Loaded extension '%s'.", instance.name)
    except Exception as exc:  # pylint: disable=broad-except # noqa: BLE001
        if strict:
            raise exc from None
        logger.exception("Failed to load extension '%s': %s", path, exc)
        call_ktrigger(
            IKernelTrigger.on_error,
            message=format_str(
                _("Failed to load extension '${{name}}': ${{exc}}."),
                fmt={"name": make_pretty(path), "exc": str(exc)},
            ),
        )


def load_all_extensions() -> None:
    """Load all extensions."""
    autoruns = config_file.get("autoruns", [])
    autoruns = list(set(autoruns))

    logger.info("Trying to load all extensions: %s ...", autoruns)

    # Load the workspace extensions.
    try:
        for path in WORKSPACE_EXTENSIONS_VENV_DIR.iterdir():
            if path.is_dir() and path.name in autoruns:
                load_extension(path)
    except OSError as exc:
        logger.warning("Failed to load workspace extensions: %s", exc)

    # Load the user extensions.
    try:
        for path in USER_EXTENSIONS_VENV_DIR.iterdir():
            if path.is_dir() and path.name in autoruns:
                load_extension(path)
    except OSError as exc:
        logger.warning("Failed to load user extensions: %s", exc)

    # Load the global extensions.
    try:
        for path in GLOBAL_EXTENSIONS_VENV_DIR.iterdir():
            if path.is_dir() and path.name in autoruns:
                load_extension(path)
    except OSError as exc:
        logger.warning("Failed to load global extensions: %s", exc)


_set_extloader(load_extension)  # Avoid circular import.
