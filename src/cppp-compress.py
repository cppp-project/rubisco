#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2023 The C++ Plus Project.
# This file is part of the cppp-repoutils library.
#
# This file is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# This file is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
C++ Plus repository distributing, packaging and initialization utilities.

This module provides the compressing utilities.
"""

import argparse

try:
    import gettext
except ImportError:
    def _(s):
        return s


import logging
import subprocess
import os
import shutil
import sys

# Application name
APP_NAME = "cppp-compress"

# Application version.
APP_VERSION = (0, 1, 0)

# Text domain
TEXT_DOMAIN = "cppp-repoutils"

# Gettext initialization.
LOCALE_DIR = os.path.join(os.path.dirname(__file__), "../share/locale")
if not os.path.exists(LOCALE_DIR):
    LOCALE_DIR = os.path.join(os.path.dirname(__file__), "../locale")
if not os.path.exists(LOCALE_DIR):
    LOCALE_DIR = "/usr/share/locale"
gettext.bindtextdomain(TEXT_DOMAIN, LOCALE_DIR)
gettext.textdomain(TEXT_DOMAIN)
_ = gettext.gettext

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("[%(asctime)s %(levelname)s] %(message)s")
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)
stream_handler.setStream(sys.stderr)
logger.addHandler(stream_handler)


def colorize_output(file, color, text, end="\n"):
    """Colorize the output text.

    Args:
        file (file): The output file.
        color (str): The color of the output text.
        text (str): The output text.
        end (str): The end of the output text. (Default value is '\\n')
    """

    color_id = 0
    if color == "red":
        color_id = 31
    elif color == "green":
        color_id = 32
    elif color == "yellow":
        color_id = 33
    elif color == "blue":
        color_id = 34
    elif color == "magenta":
        color_id = 35
    elif color == "cyan":
        color_id = 36
    elif color == "gray":
        color_id = 90
    elif color == "white":
        color_id = 37
    file.write("\033[1;%sm%s\033[0m" % (color_id, text + end))


def exec_command(commands):
    """Execute the command in the shell.

    Args:
        commands: The command to execute.

    Returns:
        bool: True if the command is executed successfully, otherwise False.
    """

    try:
        colorize_output(sys.stdout, "cyan", str(commands) + "\n")
        subprocess.check_call(commands)
    except subprocess.CalledProcessError:
        return False
    return True


def compress_tar(target, output_pkg_dir, start_dir):
    """Compress the target into a tar archive using bsdtar.

    Args:
        target (str): Target file or directory.
        output_pkg_dir (str): Output package directory.
        start_dir (str): The start directory.
    """

    output_file = "%s.tar" % os.path.basename(target)
    assert exec_command(
        [
            "bsdtar",
            "-c",
            "-v",
            "-f",
            output_file,
            "-C",
            start_dir,
            os.path.relpath(target, start_dir),
        ]
    )
    output_pkg_path = os.path.join(output_pkg_dir, output_file)
    shutil.move(output_file, output_pkg_path)
    logger.info(
        _("Compressed {type}: '{path}'.").format(type="Tar", path=output_pkg_path)
    )


def compress_archive(target, compress_type, output_pkg_dir, start_dir):
    """Compress the target into a archive.

    Args:
        target (str): Target file or directory.
        compress_type (str): The type of the archive.
        output_pkg_dir (str): Output package directory.
        start_dir (str): The start directory.
    """

    if compress_type == "tar":
        # The tar support of 7-Zip is not good, it may cause permission problems.
        compress_tar(target, output_pkg_dir, start_dir)
        return

    ext_map = {"gzip": "gz"}
    output_file = "%s.%s" % (
        os.path.basename(target),
        ext_map.get(compress_type, "" + compress_type),
    )
    assert exec_command(
        ["7z", "a", "-t" + compress_type, "-mx9", "-w" + start_dir, output_file, target]
    )
    output_pkg_path = os.path.join(output_pkg_dir, output_file)
    shutil.move(output_file, output_pkg_path)
    type_name = {"gzip": "GZip", "xz": "XZ", "zip": "ZIP", "7z": "7-Zip"}
    logger.info(
        _("Compressed {type}: '{path}'.").format(
            type=type_name.get(compress_type, "archive"), path=output_pkg_path
        )
    )


class HelpFormatter(argparse.HelpFormatter):
    """The help formatter."""

    def _format_action_invocation(self, action):
        if not action.option_strings:
            return super()._format_action_invocation(action)
        if action.dest == "help":
            action.help = _("Show this help message and exit.")
        default = self._get_default_metavar_for_optional(action)
        args_string = self._format_args(action, default)
        return ", ".join(action.option_strings) + " " + args_string

    def _format_usage(self, usage, actions, groups, prefix):
        return (
            super()
            ._format_usage(usage, actions, groups, prefix)
            .replace("usage:", _("Usage:"))
        )

    def format_help(self) -> str:
        help_text = super().format_help()
        help_text = help_text.replace(
            "positional arguments:", _("Positional arguments:")
        )
        help_text = help_text.replace("options:", _("Options:"))
        return help_text


arg_parser = argparse.ArgumentParser(
    description=_("Compressing utilities."), formatter_class=HelpFormatter
)
arg_parser.add_argument("--type", "-t", help=_("The type of the archive."))
arg_parser.add_argument(
    "--start-dir", "-s", default=".", help=_("The start directory."), dest="start_dir"
)
arg_parser.add_argument("target", help=_("Target file or directory."))
arg_parser.add_argument(
    "--output-dir",
    "-d",
    default=".",
    help=_("Output package directory."),
    dest="output_pkg_dir",
)


if __name__ == "__main__":
    try:
        args = arg_parser.parse_args()
        if not os.path.exists(args.target):
            logger.error(
                _("Target '{target}' does not exist.").format(target=args.target)
            )
            sys.exit(1)
        if not os.path.exists(args.output_pkg_dir):
            os.makedirs(args.output_pkg_dir)
        compress_archive(args.target, args.type, args.output_pkg_dir, args.start_dir)
    except KeyboardInterrupt:
        logger.error(_("Interrupted by user."))
        sys.exit(2)
    except AssertionError:
        logger.error(_("Compressing failed."))
        sys.exit(1)
    except OSError as err:
        logger.error(_("Error: {error}").format(error=err))
        sys.exit(1)
