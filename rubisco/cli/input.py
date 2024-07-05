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
Ask for user input.
"""

import rich

from rubisco.cli.output import output_warning
from rubisco.lib.exceptions import RUValueException
from rubisco.lib.l10n import _

__all__ = ["ask_yesno"]


def ask_yesno(message: str, default: bool | None = None) -> bool:
    """Ask the user a yes/no question.

    Args:
        message (str): The message to display.
        default (bool, optional): The default value. Defaults to False.

    Returns:
        bool: True if the user answered yes.
    """

    for i in range(15):  # pylint: disable=unused-variable
        choise = "(y/n)"

        if default is True:
            choise = "([green]Y[/green]/n)"
        elif default is False:
            choise = "(y/[red]N[/red])"

        rich.print(message, choise, end=" ")

        try:
            res = input().strip().lower()

            if res in ("y", "yes"):
                return True
            if res in ("n", "no"):
                return False
            if not res and default is not None:
                return default
        except EOFError as exc:
            if default is not None:
                rich.print("Y" if default else "N")
                return default
            raise KeyboardInterrupt from exc

        output_warning(
            _(
                "[yellow]Invalid input. Please enter '[green]Y"
                "[/green]' or '[red]N[/red]'.",
            )
        )

    if default is not None:
        return default
    raise RUValueException(_("Invalid input."))
