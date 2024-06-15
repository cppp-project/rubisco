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
Repoutils exceptions definitions.
These exceptions is used to describe a exception that has a document link or a
hint.
"""

import os

from repoutils.lib.l10n import _
from repoutils.lib.variable import format_str

__all__ = [
    "RUException",
    "RUValueException",
    "RUOSException",
    "RUShellExecutionException",
]


class RUException(RuntimeError):
    """
    Repoutils exception basic class.
    """

    docurl: str
    hint: str

    def __init__(self, *args, docurl: str = "", hint: str = "", **kwargs):
        """Initialize a basic repoutils exception.

        Args:
            docurl (str, optional): Document link url. Defaults to "".
            hint (str, optional): Exception hint. Defaults to "".
        """
        self.docurl = docurl
        self.hint = hint
        super().__init__(*args, **kwargs)


class RUValueException(RUException, ValueError):
    """
    Repoutils value exception.
    """


class RUOSException(RUException, OSError):
    """
    OS Exception.
    """

    def __init__(
        self,
        *args,
        errno: int = 0,
        is_winerr: bool = False,
        docurl: str = "",
        hint: str = "",
        **kwargs,
    ):
        """Initialize a operating system exception.

        Args:
            errno (int, optional): Errno value (or WinError). Defaults to 0.
            is_winerr (bool, optional): If errno is a WinError errcode. Set it
                to True. Defaults to False.
            docurl (str, optional): Document link url. Defaults to "".
            hint (str, optional): Exception hint. Defaults to "".
        """

        super().__init__(*args, docurl=docurl, hint=hint, **kwargs)
        self.errno = errno
        if is_winerr:
            self.winerror = errno


class RUShellExecutionException(RUException):
    """
    Shell execution exception.
    """

    if os.name == "nt":
        RETCODE_COMMAND_NOT_FOUND = 9009
    else:
        RETCODE_COMMAND_NOT_FOUND = 127

    retcode: int

    def __init__(self, *args, retcode: int = 0, **kwargs):
        """Initialize a shell execution exception.

        Args:
            retcode (int, optional): Shell return code. Defaults to 0.
        """

        hint = format_str(
            _("Subprocess return code is ${{retcode}}."),
            fmt={
                "retcode": str(retcode),
            },
        )
        if retcode == self.RETCODE_COMMAND_NOT_FOUND:
            hint = format_str(
                _(
                    "Subprocess return code is ${{retcode}}. "
                    "It may be caused by command not found."
                ),
                fmt={"retcode": str(retcode)},
            )

        super().__init__(hint=hint, *args, **kwargs)
        self.retcode = retcode
