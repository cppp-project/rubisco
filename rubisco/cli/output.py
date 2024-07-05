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
C++ Plus Rubisco CLI output utils.
"""

import json5 as json
import rich

from rubisco.lib.exceptions import RUException
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.variable import format_str

__all__ = [
    "push_level",
    "pop_level",
    "output_step",
    "output_error",
    "output_warning",
    "output_hint",
    "show_exception",
]


output_step_level = 0  # pylint: disable=invalid-name


def push_level() -> None:
    """Increase the output level."""

    global output_step_level  # pylint: disable=global-statement
    output_step_level += 1


def pop_level() -> None:
    """Decrease the output level."""

    global output_step_level  # pylint: disable=global-statement
    output_step_level -= 1


def output_step(message: str, level: int = -1) -> None:
    """Output a step message.

    Args:
        message (str): Message.
        level (int): Message level. The effect is as follows:
            => Level 0 message.
                :: Level 1 message.
                :: Level 1 message.
                    :: Level 2 message.
            => Level 0 message.
            If it's -1, it will be determined by push_level() and pop_level().
    """

    if level == -1:
        level = output_step_level

    if message.strip():
        prompt = "=>" if level == 0 else "::"
        indentation = "    " * level

        rich.print(
            format_str(
                "${{indentation}}[blue]${{prompt}}[/blue] [bold]${{msg}}[/bold]",  # noqa: E501
                fmt={
                    "indentation": indentation,
                    "prompt": prompt,
                    "msg": message,
                },
            ),
        )


def output_error(message: str) -> None:
    """Output an error message.

    Args:
        message (str): Message.
    """

    rich.print(
        format_str(_("[red]Error: ${{msg}}[/red]"), fmt={"msg": message}),
    )


def output_warning(message: str) -> None:
    """Output a warning message.

    Args:
        message (str): Message.
    """

    rich.print(
        format_str(
            _("[yellow]Warning: ${{msg}}[/yellow]"),
            fmt={"msg": message},
        ),
    )


def output_hint(message: str) -> None:
    """Output a hint message.

    Args:
        message (str): Message.
    """

    rich.print(
        format_str(
            _("[italic][magenta]Hint:[/magenta] ${{msg}}[/italic]"),
            fmt={"msg": message},
        ),
    )


def show_exception(exc: Exception, as_warn: bool = False) -> None:
    """Show an exception. If it has docurl or hint, show it also.

    Args:
        exc (Exception): Exception object.
        as_warn (bool, optional): Show it as a warning. Defaults to False.
    """

    logger.exception(exc)
    hint = getattr(exc, "hint", None)
    docurl = getattr(exc, "docurl", None)
    message = str(exc)
    typestr = type(exc).__name__

    if as_warn:
        perror = output_warning
    else:
        perror = output_error

    if isinstance(exc, RUException | ValueError | AssertionError):
        if not message:
            message = _("Unknown error.")
        perror(message)
    elif isinstance(exc, KeyboardInterrupt):
        perror(_("Interrupted by user."))
    elif isinstance(exc, OSError):
        perror(message)
    elif isinstance(exc, json.JSON5DecodeError):
        perror(_("JSON5 decode error."))
        perror(message)
        output_hint(_("Is may caused by a invalid JSON5 configuration file."))
    elif isinstance(exc, KeyError):
        perror(
            format_str(
                _("Missing key: ${{msg}}"),
                fmt={"msg": message},
            )
        )
        output_hint(_("Is may caused by a invalid configuration file."))
    elif isinstance(exc, SystemExit):
        raise exc
    else:
        perror(
            format_str(
                _("Internal error: ${{type}}: ${{msg}}"),
                fmt={"type": typestr, "msg": message},
            )
        )
    if hint:
        output_hint(hint)
    if docurl:
        output_hint(format_str(_("See: ${{url}}"), fmt={"url": docurl}))
