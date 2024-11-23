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

"""C++ Plus Rubisco CLI output utils."""

from __future__ import annotations

import json5 as json
import rich

from rubisco.lib.exceptions import RUError
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.variable import AFTypeError, format_str

__all__ = [
    "get_prompt",
    "output_error",
    "output_hint",
    "output_line",
    "output_step",
    "output_warning",
    "pop_level",
    "push_level",
    "show_exception",
    "sum_level_indent",
]


step_level: int = 0  # pylint: disable=invalid-name


def push_level() -> None:
    """Increase the output step level."""
    global step_level  # pylint: disable=global-statement # noqa: PLW0603
    step_level += 1


def pop_level() -> None:
    """Decrease the output level."""
    global step_level  # pylint: disable=global-statement # noqa: PLW0603
    step_level -= 1


def sum_level_indent(level: int) -> str:
    """Sum the indent of the level.

    Args:
        level (int): Message level. If it <= -1, it will be set to
        `step_level - level - 1`.

    Returns:
        str: Indent string. Only contains spaces.

    """
    if level <= -1:
        level = step_level - level - 1
    return "    " * level


def output_line(message: str, level: int = -1, end: str = "\n") -> None:
    r"""Output a line message with level.

    Args:
        message (str): Message.
        level (int): Message level. If it <= -1, it will be set to
        `step_level - level - 1`.
        end (str, optional): End of the message. Defaults to "\n".

    """
    indent = sum_level_indent(level)
    rich.print(f"{indent}{message}", end=end, flush=True)


def get_prompt(level: int, style1: str = "=>", style2: str = "::") -> str:
    """Get the prompt of the level.

    Args:
        level (int): Message level.
        style1 (str, optional): Style of level 0. Defaults to "=>".
        style2 (str, optional): Style of other levels. Defaults to "::".

    Returns:
        str: Prompt string.

    """
    if level <= -1:
        level = step_level - level - 1
    return f"[blue]{style1}[/blue]" if level == 0 else f"[blue]{style2}[/blue]"


def output_step(message: str, level: int = -1, end: str = "\n") -> None:
    r"""Output a step message.

    Args:
        message (str): Message.
        level (int): Message level. If it <= -1, it will be set to
        `step_level - level - 1`. The effect is as follows:
        ```
            => Level 0 message.
                :: Level 1 message.
                :: Level 1 message.
                    :: Level 2 message.
            => Level 0 message.
        ```
        end (str, optional): End of the message. Defaults to "\n".

    """
    if message.strip():
        indent = sum_level_indent(level)
        prompt = get_prompt(level)

        rich.print(
            format_str(
                "${{indent}}[blue]${{prompt}}[/blue] [bold]${{msg}}[/bold]",
                fmt={
                    "indent": indent,
                    "prompt": prompt,
                    "msg": message,
                },
            ),
            end=end,
            flush=True,
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


def show_exception(
    exc: Exception | KeyboardInterrupt,
    as_warn: bool = False,  # noqa: FBT001 FBT002
) -> None:
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

    perror = output_warning if as_warn else output_error

    if isinstance(exc, RUError | ValueError | AFTypeError | AssertionError):
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
            ),
        )
        output_hint(_("Is may caused by a invalid configuration file."))
    elif isinstance(exc, SystemExit):
        raise exc
    else:
        perror(
            format_str(
                _("Internal error: ${{type}}: ${{msg}}"),
                fmt={"type": typestr, "msg": message},
            ),
        )

    if hint:
        output_hint(hint)
    if docurl:
        output_hint(format_str(_("See: ${{url}}"), fmt={"url": docurl}))
