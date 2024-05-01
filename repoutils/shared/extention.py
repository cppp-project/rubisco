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
from repoutils.lib.version import Version
from repoutils.shared.ktrigger import IKernelTrigger

__all__ = ["IRUExtention"]


class IRUExtention:
    """
    Repoutils extentions interface.
    """

    name: str
    description: str
    version: Version
    ktrigger: IKernelTrigger

    def __init__(self) -> None:
        """
        Constructor. Please DO NOT initialize the extentions here.
        """

    def extention_can_load_now(self) -> bool:
        """
        Check if the extentions can load now. Some extentionss may initialize
        optionally like 'CMake' or 'Rust'.

        This method MUST be implemented by the subclass.

        Raises:
            NotImplementedError: Raise if the method is not implemented.

        Returns:
            bool: True if the extentions can load now, otherwise False.
        """

        raise NotImplementedError

    def on_load(self) -> None:
        """
        Load the extentions.
        Initialize the extentions here.

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


# A basic extention contains these modules or variables:
#   - extention/        directory    ---- The extention directory.
#       - __init__.py   file         ---- The extention module.
#           - instance  IRUExtention ---- The extention instance

def load_extentions(path: Path | str) -> None:
    """Load the extentions.

    Args:
        path (Path | str): The path of the extentions or it's name.
            If the path is a name, the extentions will be loaded from the
            default extentions directory.
    """

    if isinstance(path, str):
        path = Path(path)
