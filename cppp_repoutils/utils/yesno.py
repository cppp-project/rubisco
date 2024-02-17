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
    fmt: dict[str, str] = None,
    color: str = "",
) -> bool:
    """Ask yes or no.

    Args:
        prompt (str): The prompt message.
        default (int, optional): The default answer. -1 means
            no default answer. 0 means NO, 1 means YES.

    Returns:
        bool: True if the answer is yes, False otherwise.
    """

    logger.info("Asking question to user: '%s'", prompt)
    output(prompt, end=" ", suffix=suffix, fmt=fmt, color=color)
    inp: str = None
    match (default):
        case -1:  # No default answer.
            try:
                inp = input("[y/n] ").strip().upper()
            except EOFError:
                logger.critical("EOFError, interrupt.")
                output(_("EOFError, interrupt."), color="red")
                raise
        case 0:  # Default answer is NO.
            try:
                inp = input("[y/N] ").strip().upper()
            except EOFError:
                logger.warning("EOFError, but we have default answer 'N'.")
                inp = ""
            if not inp:
                logger.info("Return NO.")
                return False
        case 1:  # Default answer is YES.
            try:
                inp = input("[Y/n] ").strip().upper()
            except EOFError:
                logger.warning("EOFError, but we have default answer 'Y'.")
                inp = ""
            if not inp:
                logger.info("Return YES.")
                return True

    if inp == "Y":
        logger.info("Return YES.")
        return True
    if inp == "N":
        logger.info("Return NO.")
        return False

    output(_("Invalid input, please input 'Y' or 'N'."), color="yellow")
    logger.warning("Invalid input, please input 'Y' or 'N'.")
    return yesno(prompt, default=default, suffix=suffix, fmt=fmt, color=color)


if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    try:
        res = yesno("Q1: Without default answer", default=-1)
        print("=> Result:", res)
        res = yesno("Q2: Default answer is NO", default=0)
        print("=> Result:", res)
        res = yesno("Q3: Default answer is YES", default=1)
        print("=> Result:", res)
    except EOFError:
        print("=> EOF caught.")
    except KeyboardInterrupt:
        print("=> KeyboardInterrupt caught.")
