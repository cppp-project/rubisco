# -*- coding: utf-8 -*-
# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2024 The C++ Plus Project.
# This file is part of the cppp-repoutils.
#
# cppp-repoutils is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# cppp-repoutils is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Ask yes or no.
"""

__all__ = ["yesno"]

from cppp_repoutils.utils.output import output
from cppp_repoutils.utils.nls import _
from cppp_repoutils.utils.log import logger


# WHY FUCKING PYLINT REPORT THIS?
def yesno(  # pylint: disable=too-many-arguments
    prompt: str,
    default: int,
    suffix: str = "",
    fmt: dict[str, str] | None = None,
    color: str = "",
) -> bool:
    """Ask yes or no.

    Args:
        default (int): The default answer. -1 means no default answer.
            0 means NO, 1 means YES.
        suffix (str, optional): Prompt suffix. Defaults to "".
        fmt (dict[str, str] | None, optional): Prompt message format.
            Defaults to None.
        color (str, optional): Prompt message color. Defaults to "".

    Returns:
        bool: True if the answer is yes, False otherwise.

    Raises:
        EOFError: When stdin is EOF and no default answer.
    """

    while True:
        logger.info("Asking question to user: '%s'", prompt)
        output(prompt, end=" ", suffix=suffix, fmt=fmt, color=color)
        inp: str = ""
        match (default):
            case -1:  # No default answer.
                inp = input("[y/n] ").strip().upper()
            case 0:  # Default answer is NO.
                try:
                    inp = input("[y/N] ").strip().upper()
                except EOFError:
                    logger.warning("EOFError, but we have default answer 'N'.")
                    output("N")
                    inp = "N"
            case 1:  # Default answer is YES.
                try:
                    inp = input("[Y/n] ").strip().upper()
                except EOFError:
                    logger.warning("EOFError, but we have default answer 'Y'.")
                    output("Y")
                    inp = "Y"

        if inp == "Y":
            logger.info("Return YES.")
            return True
        if inp == "N":
            logger.info("Return NO.")
            return False
        if default != -1:
            return bool(default)

        output(_("Invalid input, please input 'Y' or 'N'."), color="yellow")
        logger.warning("Invalid input (only 'Y'/'N' supported).")


if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    from cppp_repoutils.utils.output import output_step

    try:
        res = yesno(  # pylint: disable=invalid-name
            "Q1: Without default answer", default=-1
        )
        output_step(f"Result: '{res}'")

        res = yesno(  # pylint: disable=invalid-name
            "Q2: Default answer is NO", default=0
        )
        output_step(f"Result: '{res}'")

        res = yesno(  # pylint: disable=invalid-name
            "Q3: Default answer is YES", default=1
        )
        output_step(f"Result: '{res}'")

    except EOFError:
        output_step("EOF caught.")
    except KeyboardInterrupt:
        output_step("KeyboardInterrupt caught.")
