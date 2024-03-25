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

# Usage: repoutils [OPTIONS] COMMAND [ARGS]...
#
#   C++ Plus Project Repository Utilities
#
# Options:
#   -h, --help  Show this message and exit
#
# Commands:
#   init        Initialize a new repository
#   show        Show repository information
#

"""
cppp-repoutils CLI entry point.
"""

import argparse
import sys
import signal

from cppp_repoutils.constants import APP_VERSION_STRING
from cppp_repoutils.utils.nls import _
from cppp_repoutils.utils.log import logger
from cppp_repoutils.utils.output import (
    output,
    output_warning,
    output_hint,
    output_error,
)
from cppp_repoutils.utils.package import (
    Package,
    SETUPSTAT_NOTSETUP,
    SETUPSTAT_SUCCESS,
    SETUPSTAT_FAILED,
)
from cppp_repoutils.utils.shell_command import (
    COMMAND_NOT_FOUND_ERROR,
    CommandExecutionError,
)

# This object will be init in main()
current_package: Package


def show_version() -> None:
    """
    Show the version of the application.
    """

    logger.debug("show_version() called.")
    output(
        "{white}{bold}repoutils{reset} "
        "(cppp-repoutils {white}{bold}{version}{reset})",
        fmt={"version": APP_VERSION_STRING},
    )
    output("C++ Plus Project Repository Utilities", color="green")
    output(_("Copyright (C) 2024 The C++ Plus Project"))
    output(
        _(
            "License {white}{bold}GPLv3+{reset}: GNU GPL version "
            "{white}{bold}3{reset} or later"
        )
    )
    output(
        _(
            "This is free software: you are free to change and redistribute it."  # noqa: E501
        )
    )
    output(
        _(
            "There is {yellow}NO WARRANTY{reset}, to the extent permitted by law."  # noqa: E501
        )
    )
    output(_("Written by ChenPi11."))


def show_package() -> None:
    """
    Show current package info.
    """

    output(
        _("Package: {white}{bold}{name}{reset}"),
        fmt={"name": current_package.name},
    )
    output(
        _("Version: {white}{bold}{version}{reset}"),
        fmt={"version": current_package.version},
    )
    authors = current_package.authors or [_("Unknown")]
    output(
        _("Author(s): {white}{bold}{author}{reset}"),
        fmt={"author": ", ".join(authors)},
    )
    output(
        _("Homepage: {white}{bold}{homepage}{reset}"),
        fmt={"homepage": current_package.homepage},
    )
    output(
        _("License: {white}{bold}{license}{reset}"),
        fmt={"license": current_package.license},
    )
    output(
        _("Tags: {white}{bold}{tags}{reset}"),
        fmt={"tags": ", ".join(current_package.tags)},
    )
    output(
        _("Description: {white}{bold}{desc}{reset}"),
        fmt={"desc": current_package.desc},
    )
    if current_package.subpackages:
        output(_("Subpackages:"))
        error_count = 0
        notsetup_count = 0
        for subpkg in current_package.subpackages:
            line = _(
                "  - {name}{reset} ({white}{bold}{type}{reset}) [{status}]"
            )  # noqa: E501
            status = {
                SETUPSTAT_NOTSETUP: _("{yellow}{bold}Not setup{reset}"),
                SETUPSTAT_SUCCESS: _("{green}{bold}Success{reset}"),
                SETUPSTAT_FAILED: _("{red}{bold}Setup failed{reset}"),
            }
            name_color = {
                SETUPSTAT_NOTSETUP: "{yellow}{bold}",
                SETUPSTAT_SUCCESS: "{green}{bold}",
                SETUPSTAT_FAILED: "{red}{bold}",
            }
            output(
                line,
                fmt={
                    "name": f"{name_color[subpkg.setup_stat()]}{subpkg.name}",
                    "type": subpkg.pkgtype,
                    "status": status[subpkg.setup_stat()],
                },
            )
            if subpkg.setup_stat() == SETUPSTAT_FAILED:
                error_count += 1
            elif subpkg.setup_stat() == SETUPSTAT_NOTSETUP:
                notsetup_count += 1
        output("")
        if error_count:
            output_warning(
                _("There are {count} subpackages failed to setup."),
                fmt={"count": str(error_count)},
            )
        if notsetup_count:
            output_warning(
                _("There are {count} subpackages not setup."),
                fmt={"count": str(notsetup_count)},
            )


def deinit_subpkgs() -> None:
    """
    Deinitialize all subpackages.
    """

    output_warning(_("You are about to remove all subpackages."))
    output_warning(_("This action is {red}IRREVERSIBLE{yellow}."))
    output_warning(_("You will lose {red}ALL{yellow} changes in subpackages."))
    output_warning(_("You should know what you are doing!"))
    output(
        _("If you really want to do this, type [{red}Do what I say{reset}]: "),
        end="",
    )
    if input() == "Do what I say":
        current_package.deinit_subpkgs()
        output(_("All subpackages removed."))
    else:
        output(_("Aborted."))


class MyArgumentParser(argparse.ArgumentParser):
    """
    Customized ArgumentParser.
    """

    def format_help(self):
        msg = super().format_help()
        msg = msg.replace("usage:", _("Usage:"))
        msg = msg.replace(
            "positional arguments:",
            _("Positional arguments:"),
        )
        msg = msg.replace("optional arguments:", _("Optional arguments:"))
        msg = msg.replace(
            "show this help message and exit",
            _("Show this help message and exit"),
        )
        msg = msg.replace("options:", _("Options:"))
        return msg

    def format_usage(self):
        msg = super().format_usage()
        msg = msg.replace("usage:", _("Usage:"))
        return msg

    def error(self, message: str) -> None:
        message = message.replace(
            "unrecognized arguments:",
            _("Unrecognized arguments:"),
        )
        self.print_usage(sys.stderr)
        args = {"prog": self.prog, "message": message}
        self.exit(2, _("%(prog)s: error: %(message)s\n") % args)


arg_parser = MyArgumentParser(
    description=_("C++ Plus Project Repository Utilities"),
)

subparser = arg_parser.add_subparsers(
    title=_("Commands"),
    description=_("Available commands"),
    dest="command",
)

arg_parser.add_argument(
    "--version",
    "-V",
    action="store_true",
    default=False,
    help=_("Print the version of the application"),
    dest="version",
)

# This argument is forcibly parsed by the log module.
arg_parser.add_argument(
    "--enable-log",
    action="store_true",
    default=False,
    help=_("Enable log output"),
)

subparser.add_parser("show", help=_("Show the repository information"))
subparser.add_parser("fetch", help=_("Fetch all subpackages"))
subparser.add_parser("deinit", help=_("Remove all subpackages"))


def main() -> int:  # pylint: disable=too-many-return-statements
    """Main entry point.

    Returns:
        int: The exit code of the application.
    """

    try:
        # Some times global-statement is very useful.
        global current_package  # pylint: disable=global-statement
        current_package = Package()

        parsed_args = arg_parser.parse_args()
        if parsed_args.version:
            show_version()
            return 0
        if parsed_args.command == "show":
            show_package()
            return 0
        if parsed_args.command == "fetch":
            current_package.setup_subpkgs()
            return 0
        if parsed_args.command == "deinit":
            deinit_subpkgs()
            return 0

        arg_parser.print_help()
        return 1
    except SystemExit as exc:
        raise exc from exc
    except KeyboardInterrupt:
        output(_("Interrupted by user."), suffix="\n", color="red")
        logger.info("Interrupted by user.")
        return signal.SIGINT
    except AssertionError as exc:
        output_error(str(exc))
        return 1
    except CommandExecutionError as exc:
        output(
            _("Command '{cmd}' failed with return code {retcode}."),
            fmt={"cmd": exc.cmd, "retcode": str(exc.returncode)},
            suffix="\n",
            color="red",
        )
        if exc.returncode == COMMAND_NOT_FOUND_ERROR:
            output_hint(
                _(
                    "The returned code is '{code}'. It may mean that the command is not found."  # noqa: E501 # pylint: disable=line-too-long
                ),
                fmt={"code": str(exc.returncode)},
            )
        return exc.returncode


if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    sys.exit("Please run repoutils.__main__ instead of repoutils.cli")
