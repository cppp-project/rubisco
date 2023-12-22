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
import logging
import subprocess
import os
import shutil
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("[%(asctime)s %(levelname)s] %(message)s")
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)
stream_handler.setStream(sys.stderr)
logger.addHandler(stream_handler)


def colorize_output(file, color, text):
    """Colorize the output text.

    Args:
        file (file): The output file.
        color (str): The color of the output text.
        text (str): The output text.
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
    file.write("\033[1;%sm%s\033[0m" % (color_id, text))


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
    logger.info('Compressed tar: "%s".', output_pkg_path)


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
    type_name = {"tar": "Tar", "gzip": "GZip", "xz": "XZ", "zip": "ZIP", "7z": "7-Zip"}
    logger.info(
        'Compressed %s: "%s".', type_name.get(compress_type, "archive"), output_pkg_path
    )


arg_parser = argparse.ArgumentParser(description="Compressing utilities.")
arg_parser.add_argument("--type", help="The type of the archive.")
arg_parser.add_argument("-C", default=".", help="The start directory.")
arg_parser.add_argument("target", help="Target file or directory.")
arg_parser.add_argument("output_pkg_dir", help="Output package directory.")

if __name__ == "__main__":
    try:
        args = arg_parser.parse_args()
        if not os.path.exists(args.target):
            logger.error('Target "%s" does not exist', args.target)
            sys.exit(1)
        if not os.path.exists(args.output_pkg_dir):
            os.makedirs(args.output_pkg_dir)
        compress_archive(args.target, args.type, args.output_pkg_dir, args.C)
    except KeyboardInterrupt:
        logger.error("Interrupted by user.")
        sys.exit(2)
    except AssertionError:
        logger.error("Compressing failed.")
        sys.exit(1)
    except OSError as err:
        logger.error("Error: %s", err)
        sys.exit(1)
