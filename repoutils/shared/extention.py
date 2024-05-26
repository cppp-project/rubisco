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
Repoutils extentions interface.
"""

from __future__ import absolute_import

from pathlib import Path

from repoutils.config import (GLOBAL_EXTENSIONS_DIR, USER_EXTENSIONS_DIR,
                              WORKSPACE_EXTENSIONS_DIR)
from repoutils.lib.exceptions import RUValueException
from repoutils.lib.l10n import _
from repoutils.lib.log import logger
from repoutils.lib.variable import format_str
from repoutils.lib.version import Version
from repoutils.shared.ktrigger import (IKernelTrigger, bind_ktrigger_interface,
                                       call_ktrigger)

__all__ = ["IRUExtention"]


class IRUExtention:
    """
    Repoutils extention interface.
    """

    name: str
    description: str
    version: Version
    ktrigger: IKernelTrigger

    def __init__(self) -> None:
        """
        Constructor. Please DO NOT initialize the extention here.
        """

    def extention_can_load_now(self) -> bool:
        """
        Check if the extention can load now. Some extentions may initialize
        optionally like 'CMake' or 'Rust'.

        This method MUST be implemented by the subclass.

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


invalid_ext_names = ["repoutils"]  # Avoid logger's name conflict.


# A basic extention contains these modules or variables:
#   - extention/        directory    ---- The extention directory.
#       - __init__.py   file         ---- The extention module.
#           - instance  IRUExtention ---- The extention instance
def load_extention(path: Path | str, strict: bool = False) -> None:
    """Load the extention.

    Args:
        path (Path | str): The path of the extention or it's name.
            If the path is a name, the extention will be loaded from the
            default extention directory.
        strict (bool, optional): If True, raise an exception if the extention
    """

    try:
        if isinstance(path, str):
            path = Path(path)
        path = path.absolute()

        if not path.is_dir():
            raise RUValueException(
                format_str(
                    _(
                        "The extention path '{underline}{path}{reset}' is not "
                        "a directory."
                    ),
                    fmt={"path": str(path)},
                ),
            )

        # Load the extention.
        module = __import__(path.name, fromlist=[str(path.parent)])
        if not hasattr(module, "instance"):
            raise RUValueException(
                format_str(
                    _(
                        "The extention '{underline}{path}{reset}' does not "
                        "have an instance."
                    ),
                    fmt={"path": str(path)},
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
                    _("Invalid extention name: '{underline}{name}{reset}' ."),
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
        if not instance.extention_can_load_now():
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

        instance.on_load()
        bind_ktrigger_interface(
            instance.name,
            instance.ktrigger,
        )
        logger.info("Loaded extention '%s'.", instance.name)
    except Exception as exc:  # pylint: disable=broad-except
        if strict:
            raise exc
        logger.exception("Failed to load extention '%s': %s", path, exc)
        call_ktrigger(
            IKernelTrigger.on_error,
            message=format_str(
                _("Failed to load extention '{name}': {exc}."),
                fmt={"name": str(path), "exc": str(exc)},
            ),
        )


def load_all_extentions() -> None:
    """Load all extentions."""

    # Load the workspace extentions.
    try:
        for path in WORKSPACE_EXTENSIONS_DIR.iterdir():
            if path.is_dir():
                load_extention(path)
    except OSError as exc:
        logger.warning("Failed to load workspace extentions: %s", exc)

    # Load the user extentions.
    try:
        for path in USER_EXTENSIONS_DIR.iterdir():
            if path.is_dir():
                load_extention(path)
    except OSError as exc:
        logger.warning("Failed to load user extentions: %s", exc)

    # Load the global extentions.
    try:
        for path in GLOBAL_EXTENSIONS_DIR.iterdir():
            if path.is_dir():
                load_extention(path)
    except OSError as exc:
        logger.warning("Failed to load global extentions: %s", exc)
