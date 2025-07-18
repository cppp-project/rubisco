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

"""Argument for CLI."""

import argparse
from typing import Any

from rubisco.cli.argparse_generator import gen_argparse
from rubisco.cli.cefs_dbg.cli import RubiscoCEFSDebuggerCLI
from rubisco.cli.main.help_formatter import RUHelpFormatter
from rubisco.cli.main.version_action import CLIVersionAction, version_callback
from rubisco.cli.output import output_step
from rubisco.kernel.command_event.args import Argument, Option
from rubisco.kernel.command_event.callback import EventCallback
from rubisco.kernel.command_event.event_file_data import EventFileData
from rubisco.kernel.command_event.event_path import EventPath
from rubisco.kernel.command_event.event_types import (
    EventObjectStat,
    EventObjectType,
)
from rubisco.kernel.command_event.register import EventUnit, register_events
from rubisco.lib.l10n import _

__all__ = [
    "early_arg_parser",
    "get_arg_parser",
    "init_arg_parser",
]


def cefs_callback(
    options: list[Option[Any]],  # noqa: ARG001 # pylint: disable=W0613
    args: list[Argument[Any]],  # noqa: ARG001 # pylint: disable=W0613
) -> None:
    """Launch Rubisco CommandEventFS Debugger CLI.

    Args:
        options (list[Option[Any]]): Options of command line.
        args (list[Argument[Any]]): Arguments of command line.

    """
    try:
        RubiscoCEFSDebuggerCLI().run()
    except (SystemExit, KeyboardInterrupt, EOFError):
        output_step(_("Rubisco CommandEventFS Debugger CLI exited."))


def init_arg_parser() -> None:
    """Initialize argument parser."""
    EventPath("/").event_object.set_stat(
        EventObjectStat(
            type=EventObjectType.DIRECTORY,
            options=[
                Option[str](
                    name="project-root-dir",
                    title=_("Project root"),
                    description=_("The root directory of Rubisco project."),
                    typecheck=str,
                    aliases=["root"],
                    default=".",
                ),
                Option[str](
                    name="used-prompt-colors",
                    title=_("Used prompt colors (for CLI)."),
                    description=_(
                        "Prompt colors used by rubisco parent process.",
                    ),
                    typecheck=str,
                    default="",
                ),
                Option[str](
                    name="log",
                    title=_("Log file"),
                    description=_("The file path for saving log."),
                    typecheck=str,
                    default="",
                ),
                Option[bool](
                    name="rubisco-debug",
                    title=_("Debug mode"),
                    description=_("Run rubisco in debug mode."),
                    typecheck=bool,
                    aliases=["debug"],
                    default=False,
                ),
            ],
        ),
    )

    register_events(
        [
            EventUnit(
                name="version",
                stat=EventObjectStat(
                    type=EventObjectType.FILE,
                    description=_("Show version."),
                ),
                file_data=EventFileData(
                    callbacks=[
                        EventCallback(
                            callback=version_callback,
                            description=_("Show Rubisco version."),
                        ),
                    ],
                ),
            ),
            EventUnit(
                name="cefs-debug",
                stat=EventObjectStat(
                    type=EventObjectType.FILE,
                    description=_("Launch CommandEventFS Debugger."),
                ),
                file_data=EventFileData(
                    callbacks=[
                        EventCallback(
                            callback=cefs_callback,
                            description=_(
                                "Launch Rubisco CommandEventFS Debugger CLI.",
                            ),
                        ),
                    ],
                ),
            ),
            EventUnit(
                name="ext",
                stat=EventObjectStat(
                    type=EventObjectType.DIRECTORY,
                    description=_("Extension directory."),
                ),
            ),
        ],
    )


def get_arg_parser() -> argparse.ArgumentParser:
    """Generate a new argument parser from CommandEventFS.

    Returns:
        argparse.ArgumentParser: The generated argument parser.

    """
    arg_parser = argparse.ArgumentParser(
        description="Rubisco CLI",
        formatter_class=RUHelpFormatter,
        allow_abbrev=True,
    )

    arg_parser.register("action", "version", CLIVersionAction)

    # For "rubisco --version".
    arg_parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="",
    )
    gen_argparse(EventPath("/"), arg_parser)

    return arg_parser


# Early argument parser.
early_arg_parser = argparse.ArgumentParser(
    description="Rubisco CLI",
    add_help=False,
    allow_abbrev=False,
    formatter_class=RUHelpFormatter,
)

# For "rubisco --version".
early_arg_parser.add_argument(
    "--root",
    type=str,
    help=_("Project root directory."),
    action="store",
    dest="root_directory",
)

# For "rubisco --used-colors=COLORS"
early_arg_parser.add_argument(
    "--used-prompt-colors",
    type=set,
    help=_("Prompt colors used by rubisco parent process."),
    action="store",
    default=set(),
    dest="used_prompt_colors",
)
