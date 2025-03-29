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

from rubisco.cli.main.help_formatter import RUHelpFormatter
from rubisco.cli.main.version_action import CLIVersionAction
from rubisco.lib.l10n import _

__all__ = [
    "arg_parser",
    "commands_parser",
    "extman_command_parser",
    "extman_parser",
    "hook_arg_parser",
    "hook_command_parser",
]

# Root argument parser.
arg_parser = argparse.ArgumentParser(
    description="Rubisco CLI",
    formatter_class=RUHelpFormatter,
)

arg_parser.register("action", "version", CLIVersionAction)

# For "rubisco --version".
arg_parser.add_argument(
    "-v",
    "--version",
    action="version",
    version="",
)

# For "rubisco --used-colors=COLORS"
arg_parser.add_argument(
    "--used-prompt-colors",
    type=set,
    help=_("Prompt colors used by rubisco parent process."),
    action="store",
    default=set(),
    dest="used_prompt_colors",
)

# For "rubisco --root=DIRECTORY".
arg_parser.add_argument(
    "--root",
    type=str,
    help=_("Project root directory."),
    action="store",
    dest="root_directory",
)

# For "rubisco --log=LOGFILE".
arg_parser.add_argument(
    "--log",
    action="store_true",
    help=_("Save log to the log file."),
)

# For "rubisco --debug". This argument will be parsed in "lib/log.py".
arg_parser.add_argument(
    "--debug",
    action="store_true",
    help=_("Run rubisco in debug mode."),
)

# For "rubisco --usage".
arg_parser.add_argument(
    "--usage",
    action="store_true",
    help=_("Show usage."),
)

# Rubsisco built-in command line parser.
commands_parser = arg_parser.add_subparsers(
    title=_("Available commands"),
    dest="command",
    metavar="",
    required=False,
)

# Rubisco extension manager command line parser.
extman_parser = commands_parser.add_parser(
    "ext",
    help=_("Manage extensions."),
    formatter_class=RUHelpFormatter,
)

# Extension manager command line parser.
extman_command_parser = extman_parser.add_subparsers(
    dest="command",
    required=True,
    help=_("Extension commands."),
)

# Hook argument parser.
hook_arg_parser = argparse.ArgumentParser(
    description="Rubisco CLI Hooks",
    formatter_class=RUHelpFormatter,
)

hook_command_parser = hook_arg_parser.add_subparsers(
    dest="command",
    required=True,
    help=_("Hook commands."),
)
