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
Generate shell command from a list of arguments.
"""

from subprocess import Popen
import os
import sys
from cppp_repoutils.utils.output import output

__all__ = ["command", "run_command", "COMMAND_NOT_FOUND_ERROR"]


def command(args: list[str]) -> str:
    """Generate shell command from a list of arguments.

    Args:
        command (list): The list of arguments.

    Returns:
        str: The shell command.
    """

    res_command = ""
    for arg in args:
        if '"' in arg:
            arg = arg.replace('"', '\\"')
        if " " in arg:
            res_command += f'"{arg}" '
        else:
            res_command += f"{arg} "
    return res_command.strip()


def run_command(cmd: list[str] | str) -> int:
    """Run shell command.

    Args:
        cmd (list[str] | str): The list of arguments or the shell command.

    Returns:
        int: The return code.
    """

    if isinstance(cmd, list):
        cmd = command(cmd)
    output(cmd, color="cyan")
    with Popen(cmd, shell=True, stdout=sys.stdout, stderr=sys.stderr) as proc:
        proc.wait()
        return proc.returncode


if os.name == "nt":
    COMMAND_NOT_FOUND_ERROR = 9009
else:
    COMMAND_NOT_FOUND_ERROR = 127


if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    test_cmd = ["git", "clone", "<part1> <part2>"]
    print(test_cmd)
    print()
    print(command(test_cmd))

    print("===== Returned: ", run_command(["aabbccdd", "Test: return != 0"]))

    print("===== Returned: ", run_command('echo "Test: return == 0"'))
