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
Find application program.
"""

import os
import platform
import re
import locale
import subprocess
from typing import Optional
from cppp_repoutils.utils.shell_command import command

__all__ = ["is_this_app", "which", "find_python3"]


def is_this_app(
    path: str, verinfo_format: str, verinfo_command: Optional[str] = "--version"
) -> bool:
    """Check whether the file is this application.

    Args:
        path (str): The path to the file.
        verinfo_format (str): The version information format string.
        verinfo_command (str, optional): The version information command. Defaults to "--version".

    Returns:
        bool: True if the file is a Python interpreter, otherwise False.
    """

    try:
        with subprocess.Popen(
            command([path, verinfo_command]),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding=locale.getpreferredencoding(False),
            shell=True,
        ) as pipe:
            if pipe.wait() != 0:
                return False
            version = pipe.stdout.read().strip()
            return re.match(verinfo_format, version) is not None
    except OSError:
        return False


# Which cache.
which_cache: dict[str, str] = {}


def which(program: str):
    """Get the absolute program in the PATH or current directory.

    Args:
        program (str): The program.

    Returns:
        str: The program path.
    """

    if program in which_cache:
        return which_cache[program]

    if os.access(program, os.X_OK):
        return os.path.abspath(program)
    for path in os.environ["PATH"].split(os.pathsep):
        path = path.strip('"')
        exe_file = os.path.join(path, program)
        if os.access(exe_file, os.X_OK):
            which_cache[program] = exe_file
            return os.path.abspath(exe_file)
    ext = os.path.splitext(program)[1]
    if platform.system() == "Windows" and ext != ".exe" and ext != ".com":
        # On Windows, 'xxx' may mean 'xxx.exe' or 'xxx.com' but 'xxx' is not in the PATH,
        # so we try add '.exe' or '.com' and find it again.
        result = which(program + ".exe")
        if result == program + ".exe":
            result = which(program + ".com")
        if result != program + ".com":
            return result

    return program


def find_python3() -> str:
    """Find Python3 interpreter.

    Returns:
        str: The command to execute the Python interpreter.
    """

    regex = r"Python 3\.\d+\.\d+"
    if is_this_app(os.environ.get("PYTHON3", "python3"), regex):
        return os.environ.get("PYTHON3", "python3")
    if is_this_app(os.environ.get("PYTHON", "python"), regex):
        return os.environ.get("PYTHON", "python")
    if is_this_app("python3", regex):
        return "python3"
    if is_this_app("python", regex):
        return "python"
    if is_this_app("py", regex):  # Python Launcher for Windows.
        return "py"
    return "python"


if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    print(f"which('whoami'): {which('whoami')}")
    py3_path = which("python3")
    print(f"which('python3'): {py3_path}")
    python3_checked_res = is_this_app(py3_path, r"Python 3\.\d+\.\d+")
    print(f"is_this_app(which('python3'), ...): {python3_checked_res}")
    print(f"Find Python3: {find_python3()}")
