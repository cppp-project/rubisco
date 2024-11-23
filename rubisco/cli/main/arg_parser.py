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
import os
import sys
from pathlib import Path

from rubisco.cli.main.help_formatter import RUHelpFormatter
from rubisco.cli.main.version_action import CLIVersionAction, show_version
from rubisco.cli.output import output_step
from rubisco.lib.exceptions import RUError
from rubisco.lib.l10n import _
from rubisco.lib.variable import format_str, make_pretty

__all__ = ["arg_parser", "hook_commands", "early_arg_parse"]

arg_parser = argparse.ArgumentParser(
    description="Rubisco CLI",
    formatter_class=RUHelpFormatter,
)

arg_parser.register("action", "version", CLIVersionAction)

arg_parser.add_argument(
    "-v",
    "--version",
    action="version",
    version="",
)

arg_parser.add_argument("--root", type=str, help=_("Project root directory."))

arg_parser.add_argument(
    "--log",
    action="store_true",
    help=_("Save log to the log file."),
)

arg_parser.add_argument(
    "--debug",
    action="store_true",
    help=_("Run rubisco in debug mode."),
)

arg_parser.add_argument(
    "--usage",
    action="store_true",
    help=_("Show usage."),
)

arg_parser.add_argument(
    "command",
    action="store",
    nargs="?",
    help=_("Command to run."),
    default=["info"],
)

hook_commands = arg_parser.add_subparsers(
    title=_("Available commands"),
    dest="command",
    metavar="",
    required=False,
)

hook_commands.add_parser(
    "info",
    help=_("Show project information."),
)


def early_arg_parse() -> None:
    """Parse arguments without argparse.

    Some arguments will be added to argparse later (like hooks).
    If we use argparse here, they will inoperative.
    """
    if "-h" in sys.argv or "--help" in sys.argv:
        arg_parser.print_help()
        sys.exit(0)
    if "-v" in sys.argv or "--version" in sys.argv:
        show_version()
        sys.exit(0)
    if "--usage" in sys.argv:
        arg_parser.print_usage()
        sys.exit(0)
    for idx, arg in enumerate(sys.argv):
        if arg.startswith("--root"):
            if "=" in arg:
                root = arg.split("=")[1].strip()
            else:
                if idx + 1 >= len(sys.argv):
                    arg_parser.print_usage()
                    raise RUError(
                        _("Missing argument for '--root' option."),
                    )
                root = sys.argv[idx + 1].strip()
                if root.startswith("-"):
                    arg_parser.print_usage()
                    raise RUError(
                        _("Missing argument for '--root' option."),
                    )
            if root:
                root = Path(root).absolute()
                output_step(
                    format_str(
                        _("Entering directory '${{path}}'"),
                        fmt={"path": make_pretty(str(root))},
                    ),
                )
                os.chdir(root)
