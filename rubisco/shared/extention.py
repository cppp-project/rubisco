# -*- coding: utf-8 -*-
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

"""
Rubisco extentions interface.
"""

from pathlib import Path

from rubisco.config import (GLOBAL_EXTENTIONS_DIR, USER_EXTENTIONS_DIR,
                            WORKSPACE_EXTENTIONS_DIR)
from rubisco.kernel.workflow import Step, _set_extloader, register_step_type
from rubisco.lib.exceptions import RUValueException
from rubisco.lib.l10n import _
from rubisco.lib.load_module import import_module_from_path
from rubisco.lib.log import logger
from rubisco.lib.variable import format_str, make_pretty
from rubisco.lib.version import Version
from rubisco.shared.ktrigger import (IKernelTrigger, bind_ktrigger_interface,
                                     call_ktrigger)

__all__ = ["IRUExtention"]


class IRUExtention:
    """
    Rubisco extention interface.
    """

    name: str
    description: str
    version: Version
    ktrigger: IKernelTrigger
    workflow_steps: dict[str, Step]
    steps_contributions: dict[Step, list[str]]

    def __init__(self) -> None:
        """
        Constructor. Please DO NOT initialize the extention here.
        """

    def extention_can_load_now(self, is_auto: bool) -> bool:
        """
        Check if the extention can load now. Some extentions may initialize
        optionally like 'CMake' or 'Rust'.

        This method MUST be implemented by the subclass.

        Args:
            is_auto (bool): True if the extention is loaded automatically,
                (load by `load_all_extentions`), otherwise False. (load by
                project)

        Raises:
            NotImplementedError: Raise if the method is not implemented.

        Returns:
            bool: True if the extention can load now, otherwise False.
        """

        raise NotImplementedError

    def on_load(self) -> None:
        """
        Load the extention.
        Initialize the extention here.

        This method MUST be implemented by the subclass.
        """

        raise NotImplementedError

    def reqs_is_sloved(self) -> bool:
        """
        Check if the system requirements are solved.
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
        """
        Solve the system requirements.
        This method MUST be implemented by the subclass.
        If the slution is not possible, please raise an exception here.
        It is recommended to use RUException if you have hint, docurl, etc.
        """

        raise NotImplementedError


invalid_ext_names = ["rubisco"]  # Avoid logger's name conflict.


# A basic extention contains these modules or variables:
#   - extention/        directory    ---- The extention directory.
#       - __init__.py   file         ---- The extention module.
#           - instance  IRUExtention ---- The extention instance
def load_extention(  # pylint: disable=too-many-branches
    path: Path | str,
    strict: bool = False,
    is_auto: bool = False,
) -> None:
    """Load the extention.

    Args:
        path (Path | str): The path of the extention or it's name.
            If the path is a name, the extention will be loaded from the
            default extention directory.
        strict (bool, optional): If True, raise an exception if the extention
            loading failed.
    """

    try:
        if isinstance(path, str):
            if (WORKSPACE_EXTENTIONS_DIR / path).is_dir():
                path = GLOBAL_EXTENTIONS_DIR / path
            elif (USER_EXTENTIONS_DIR / path).is_dir():
                path = USER_EXTENTIONS_DIR / path
            elif (GLOBAL_EXTENTIONS_DIR / path).is_dir():
                path = WORKSPACE_EXTENTIONS_DIR / path
            else:
                raise RUValueException(
                    format_str(
                        _(
                            "The extention '${{name}}' does not exist in"
                            " workspace, user, or global extention directory."
                        ),
                        fmt={"name": path},
                    ),
                    hint=format_str(
                        _("Try to load the extention as a path."),
                    ),
                )

        if not path.is_dir():
            raise RUValueException(
                format_str(
                    _(
                        "The extention path '[underline]${{path}}[/underline]'"
                        " is not a directory."
                    ),
                    fmt={"path": make_pretty(path.absolute())},
                ),
            )

        # Load the extention.

        try:
            module = import_module_from_path(path)
        except FileNotFoundError as exc:
            raise RUValueException(
                format_str(
                    _(
                        "The extention path '[underline]${{path}}[/underline]'"
                        " does not exist."
                    ),
                    fmt={"path": make_pretty(path.absolute())},
                ),
            ) from exc
        except ImportError as exc:
            raise RUValueException(
                format_str(
                    _(
                        "Failed to load extention '[underline]${{path}}"
                        "[/underline]'."
                    ),
                    fmt={"path": make_pretty(path.absolute())},
                ),
                hint=format_str(
                    _(
                        "Please make sure this extention is valid.",
                    ),
                ),
            ) from exc

        if not hasattr(module, "instance"):
            raise RUValueException(
                format_str(
                    _(
                        "The extention '[underline]${{path}}[/underline]' does"
                        " not have an instance."
                    ),
                    fmt={"path": make_pretty(path.absolute())},
                ),
                hint=format_str(
                    _(
                        "Please make sure this extention is valid.",
                    )
                ),
            )
        instance: IRUExtention = module.instance

        # Security check.
        if instance.name in invalid_ext_names:
            raise RUValueException(
                format_str(
                    _("Invalid extention name: '${{name}}' ."),
                    fmt={"name": instance.name},
                ),
                hint=format_str(
                    _(
                        "Please use a different name for the extention.",
                    ),
                ),
            )

        logger.info("Loading extention '%s'...", instance.name)

        # Check if the extention can load now.
        if not instance.extention_can_load_now(is_auto):
            logger.info("Skipping extention '%s'...", instance.name)
            return

        # Load the extention.
        if not instance.reqs_is_sloved():
            logger.info(
                "Solving system requirements for extention '%s'...",
                instance.name,
            )
            instance.reqs_solve()
            if not instance.reqs_is_sloved():
                logger.error(
                    "Failed to solve system requirements for extention '%s'.",
                    instance.name,
                )
                return

        # Register the workflow steps.
        for step_name, step in instance.workflow_steps:
            contributions = []
            if step in instance.steps_contributions:
                contributions = instance.steps_contributions[step]
            register_step_type(step_name, step, contributions)

        instance.on_load()
        bind_ktrigger_interface(
            instance.name,
            instance.ktrigger,
        )
        call_ktrigger(IKernelTrigger.on_extention_loaded, instance=instance)
        logger.info("Loaded extention '%s'.", instance.name)
    except Exception as exc:  # pylint: disable=broad-except
        if strict:
            raise exc from None
        logger.exception("Failed to load extention '%s': %s", path, exc)
        call_ktrigger(
            IKernelTrigger.on_warning,
            message=format_str(
                _("Failed to load extention '${{name}}': ${{exc}}."),
                fmt={"name": make_pretty(path.absolute()), "exc": str(exc)},
            ),
        )


def load_all_extentions() -> None:
    """Load all extentions."""

    # Load the workspace extentions.
    try:
        for path in WORKSPACE_EXTENTIONS_DIR.iterdir():
            if path.is_dir():
                load_extention(path, is_auto=True)
    except OSError as exc:
        logger.warning("Failed to load workspace extentions: %s", exc)

    # Load the user extentions.
    try:
        for path in USER_EXTENTIONS_DIR.iterdir():
            if path.is_dir():
                load_extention(path, is_auto=True)
    except OSError as exc:
        logger.warning("Failed to load user extentions: %s", exc)

    # Load the global extentions.
    try:
        for path in GLOBAL_EXTENTIONS_DIR.iterdir():
            if path.is_dir():
                load_extention(path, is_auto=True)
    except OSError as exc:
        logger.warning("Failed to load global extentions: %s", exc)


_set_extloader(load_extention)  # Avoid circular import.
