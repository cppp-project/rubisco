# -*- coding: utf-8 -*-
# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2024 The C++ Plus Project.
# This file is part of the repoutils.
#
# repoutils is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# repoutils is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Repoutils process control.
"""

import ctypes
import os
from pathlib import Path
from subprocess import PIPE, STDOUT, Popen

from repoutils.config import DEFAULT_CHARSET
from repoutils.lib.command import command
from repoutils.lib.exceptions import RUShellExecutionException
from repoutils.lib.fileutil import TemporaryObject
from repoutils.lib.log import logger
from repoutils.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = ["Process", "popen"]


def _win32_set_console_visiable(visiable: bool) -> None:
    if os.name == "nt":
        if visiable:
            ctypes.cdll.kernel32.FreeConsole()  # To avoid error 5 and 6.
            ctypes.cdll.kernel32.AllocConsole()
        else:
            ctypes.cdll.kernel32.FreeConsole()
        logger.debug(
            "Set console visiable to %s. GetLastError() = %s",
            visiable,
            ctypes.cdll.kernel32.GetLastError(),
        )
        ctypes.cdll.kernel32.SetLastError(0)


def get_system_shell() -> str:
    """Get the system shell.

    Returns:
        str: The system shell.
    """

    if os.name == "nt":
        return os.environ.get("COMSPEC", "cmd.exe")
    return os.environ.get("SHELL", "/bin/sh")


class Process:
    """
    Process controler. Process's stdin/stdout/stderr will be direct to
    parent process's stdin/stdout/stderr. We will allocate a new console for
    non-console application on Windows.
    """

    origin_cmd: str  # For UCI's output.
    cmd: str
    cwd: Path
    process: Popen
    _tempfile: TemporaryObject | None

    def __init__(
        self,
        cmd: list[str] | str,
        cwd: Path = Path.cwd(),
    ) -> None:
        if isinstance(cmd, str) and "\n" in cmd:
            self._tempfile = TemporaryObject.new_file()
            self._tempfile.path.write_text(
                f"{cmd}\n",
                encoding=DEFAULT_CHARSET,
            )
            self._tempfile.path.chmod(0o755)
            self.cmd = command([get_system_shell(), str(self._tempfile.path)])
        else:
            self.cmd = command(cmd)
            self._tempfile = None
        self.origin_cmd = command(cmd)
        self.cwd = cwd

    def run(self, fail_on_error: bool = True) -> int:
        """Run the process.

        Args:
            fail_on_error (bool): Raise exception on error.

        Returns:
            int: The return code.
        """

        _win32_set_console_visiable(True)
        call_ktrigger(IKernelTrigger.pre_exec_process, proc=self)
        with Popen(self.cmd, shell=True, cwd=str(self.cwd)) as self.process:
            try:
                ret = self.process.wait()
                raise_exc = ret != 0 and fail_on_error
                call_ktrigger(
                    IKernelTrigger.post_exec_process,
                    proc=self,
                    retcode=ret,
                    raise_exc=raise_exc,
                )
                if raise_exc:
                    raise RUShellExecutionException(retcode=ret)
                return ret
            finally:
                _win32_set_console_visiable(False)

    def terminate(self) -> None:
        """Terminate the process."""

        self.process.terminate()
        self.process.wait()
        _win32_set_console_visiable(False)

    def __repr__(self) -> str:
        """Return the string representation of the object.

        Returns:
            str: The string representation.
        """

        if self._tempfile:
            return f"Process({repr(self.origin_cmd)})"
        return f"Process({repr(self.cmd)})"


def popen(
    cmd: list[str] | str,
    cwd: Path = Path.cwd(),
    stdout: bool = True,
    stderr: int = 1,
    strict: bool = False,
) -> tuple[str, str, int]:
    """Run the command and return the stdout and stderr.

    Args:
        cmd (list[str] | str): The command.
        cwd (Path): The working directory.
        stdout (bool, optional): Return stdout. Defaults to True.
        stderr (int, optional): Return stderr. If 0, stderr will be ignored.
            If 1, stderr will be returned. If 2, stderr will be redirected to
            stdout. Defaults to 1.
        strict (bool, optional): Raise an exception if return code is not 0.
            Defaults to True.

    Returns:
        tuple[str, str]: The stdout and stderr. If stdout or stderr is not
            required, it will be "".

    Raises:
        RUShellExecutionException: If retcode !=0 and we are in strict mode.
    """

    temp: TemporaryObject | None = None
    if "\n" in cmd:
        temp = TemporaryObject.new_file()
        temp.path.write_text(
            f"{cmd}\n",
            encoding=DEFAULT_CHARSET,
        )
        temp.path.chmod(0o755)
        real_cmd = command([get_system_shell(), str(temp.path)])
    else:
        real_cmd = command(cmd)
    logger.debug("Popen: %s", repr(cmd))
    with Popen(
        real_cmd,
        cwd=str(cwd),
        shell=True,
        stdout=PIPE,
        stderr=None if stderr == 0 else PIPE if stderr == 1 else STDOUT,
    ) as process:
        process.wait()
        if strict and process.returncode:
            raise RUShellExecutionException(retcode=process.returncode)
        return (
            (
                process.stdout.read().decode(DEFAULT_CHARSET)  # type: ignore
                if stdout
                else ""
            ),
            (
                process.stderr.read().decode(DEFAULT_CHARSET)  # type: ignore
                if stderr == 1
                else ""
            ),
            process.returncode,
        )


if __name__ == "__main__":

    import rich

    rich.print(f"{__file__}: {__doc__.strip()}")

    # Test: Process.
    p = Process("echo Hello, world!")
    p.run()
    p = Process(["echo", "Hello, world!"])
    p.run()

    # Test: Process with error
    p = Process("echo Hello, world! && exit 1")
    try:
        p.run(fail_on_error=True)
        assert False
    except RUShellExecutionException as e:
        assert e.retcode == 1

    # Test: Process with error.
    p = Process("echo Hello, world! && exit 1")
    try:
        assert p.run(fail_on_error=False) == 1
    except RUShellExecutionException:
        assert False

    # Test: Popen.
    stdout_, stderr_, retcode_ = popen("echo Hello, world!", strict=False)
    assert stdout_ == "Hello, world!\n"
    assert stderr_ == ""
    assert retcode_ == 0

    # Test: Popen with an exception.
    try:
        stdout_, stderr_, retcode_ = popen(
            "false",
            stdout=False,
            stderr=1,
            strict=True,
        )
        assert 0
    except RUShellExecutionException:
        print("Exception caught.")

    # Test: A multiline command.
    p = Process("echo line1 \n echo line2")
    assert p.run() == 0

    # Test: A multiline popen.
    stdout_, stderr_, retcode_ = popen("echo line1 \n echo line2")
    assert stdout_.strip() == "line1\nline2"
    assert stderr_ == ""
    assert retcode_ == 0

    # Test: Popen with stderr redirection.
    stdout_, stderr_, retcode_ = popen("echo Hello, world! >&2", stderr=2)
    assert stdout_ == "Hello, world!\n"
    assert stderr_ == ""
    assert retcode_ == 0
