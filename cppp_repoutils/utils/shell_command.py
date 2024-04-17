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

from subprocess import Popen, PIPE
from pathlib import Path
import os
import sys
from cppp_repoutils.constants import DEFAULT_CHARSET
from cppp_repoutils.cli.output import output_step
from cppp_repoutils.utils.nls import _
from cppp_repoutils.utils.log import logger

__all__ = ["command", "run_command", "COMMAND_NOT_FOUND_ERROR"]

if os.name == "nt":
    COMMAND_NOT_FOUND_ERROR = 9009
else:
    COMMAND_NOT_FOUND_ERROR = 127


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


class CommandExecutionError(RuntimeError):
    """Command execution error."""

    def __init__(self, cmd: str, returncode: int):
        super().__init__(cmd, returncode)
        self.cmd = cmd
        self.returncode = returncode


def run_command(
    cmd: list[str] | str, strict: bool = True, cwd: Path | None = None
) -> int:
    """Run shell command.

    Args:
        cmd (list[str] | str): The list of arguments or the shell command.
        strict (bool): If True, raise an exception if the command returns a
            non-zero exit code.
        cwd (Path): The working directory. Default is the current working.

    Returns:
        int: The return code. If strict is True, it will always be 0.
    """

    if isinstance(cmd, list):
        cmd = command(cmd)
    output_step(_("Running command: {cyan}{cmd}{reset}"), fmt={"cmd": cmd})
    logger.debug("Running command: %s", cmd)
    if cwd:
        cwd = cwd.absolute()
    with Popen(
        cmd, shell=True, stdout=sys.stdout, stderr=sys.stderr, cwd=cwd  # noqa: E501
    ) as proc:
        proc.wait()
        if strict and proc.returncode != 0:
            raise CommandExecutionError(cmd, proc.returncode)
        return proc.returncode


def popen_command(
    cmd: list[str] | str,
    cwd: Path | None = None,
    stdout: bool = True,
    stderr: bool = True,
) -> tuple[str, str]:
    """Run shell command and return stripped stdout and stderr.

    Args:
        cmd (list[str] | str): The list of arguments or the shell command.
        cwd (Path | None, optional): The working directory. Defaults to None.
        stdout (bool, optional): Use stdout. Defaults to True.
        stderr (bool, optional): Use stderr. Defaults to True.
            If stdout and stderr are False, return an empty string.

    Returns:
        tuple[str, str]: The stdout and stderr.
    """

    if isinstance(cmd, list):
        cmd = command(cmd)
    output_step(_("Running command: {cyan}{cmd}{reset}"), fmt={"cmd": cmd})
    logger.debug("Running command: %s", cmd)
    if cwd:
        cwd = cwd.absolute()
    with Popen(
        cmd,
        shell=True,
        stdout=PIPE if stdout else sys.stdout,
        stderr=PIPE if stderr else sys.stderr,
        cwd=cwd,
        encoding=DEFAULT_CHARSET,
    ) as proc:
        retcode = proc.wait()
        if retcode != 0:
            raise CommandExecutionError(cmd, retcode)
        stdout_data, stderr_data = proc.communicate()
        return stdout_data.strip(), stderr_data.strip()


if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    test_cmd = ["git", "clone", "<part1> <part2>"]
    print(test_cmd)
    print(command(test_cmd))

    print("===== Returned: ", run_command(["", "return != 0"], strict=False))
    print("===== Returned: ", run_command('echo "return == 0"'))
