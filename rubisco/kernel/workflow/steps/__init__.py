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

"""Rubisco workflow built-in steps implementation."""

# Built-in step types.
import glob
import os
import shutil
from pathlib import Path
from typing import cast

from rubisco.envutils.env import GLOBAL_ENV, USER_ENV, WORKSPACE_ENV
from rubisco.kernel.workflow._interfaces import load_extension, run_workflow
from rubisco.kernel.workflow.step import Step
from rubisco.lib.archive import compress, extract
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.fileutil import (
    assert_rel_path,
    check_file_exists,
    copy_recursive,
    rm_recursive,
)
from rubisco.lib.l10n import _
from rubisco.lib.process import Process
from rubisco.lib.variable.utils import assert_iter_types
from rubisco.lib.variable.variable import push_variables
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = ["step_contributes", "step_types"]


class ShellExecStep(Step):
    """A shell execution step."""

    cmd: str
    cwd: Path
    fail_on_error: bool

    def init(self) -> None:
        """Initialize the step."""
        self.cmd = self.raw_data.get("run", valtype=str | list)
        if isinstance(self.cmd, list):
            assert_iter_types(
                self.cmd,
                str,
                RUValueError(
                    _("The shell command list must be a list of strings."),
                ),
            )

        self.cwd = Path(self.raw_data.get("cwd", "", valtype=str))
        self.fail_on_error = self.raw_data.get(
            "fail-on-error",
            True,
            valtype=bool,
        )

    def run(self) -> None:
        """Run the step."""
        retcode = Process(self.cmd, self.cwd).run(
            fail_on_error=self.fail_on_error,
        )
        push_variables(f"{self.global_id}.retcode", retcode)


class MkdirStep(Step):
    """Make directories."""

    paths: list[Path]

    def init(self) -> None:
        """Initialize the step."""
        paths = cast(
            "str | list[str]",
            self.raw_data.get("mkdir", valtype=str | list),
        )
        if isinstance(paths, list):
            assert_iter_types(
                paths,
                str,
                RUValueError(
                    _(
                        "The paths must be a list of strings.",
                    ),
                ),
            )
            self.paths = [Path(path) for path in paths]
        else:
            self.paths = [Path(paths)]

    def run(self) -> None:
        """Run the step."""
        for path in self.paths:
            call_ktrigger(IKernelTrigger.on_mkdir, path=path)
            assert_rel_path(path)
            path.mkdir(exist_ok=True)


class PopenStep(Step):
    """Read the output of a shell command."""

    cmd: str
    cwd: Path
    fail_on_error: bool
    stdout: bool
    stderr: int

    def init(self) -> None:
        """Initialize the step."""
        self.cmd = self.raw_data.get("popen", valtype=str)

        self.cwd = Path(self.raw_data.get("cwd", "", valtype=str))
        self.fail_on_error = self.raw_data.get(
            "fail-on-error",
            True,
            valtype=bool,
        )
        self.stdout = self.raw_data.get("stdout", True, valtype=bool)
        stderr_mode = self.raw_data.get("stderr", True, valtype=bool | str)
        if stderr_mode is True:
            self.stderr = 1
        elif stderr_mode is False:
            self.stderr = 0
        else:
            self.stderr = 2

    def run(self) -> None:
        """Run the step."""
        stdout, stderr, retcode = Process(self.cmd, cwd=self.cwd).popen(
            stdout=self.stdout,
            stderr=self.stderr,
            fail_on_error=self.fail_on_error,
            show_step=True,
        )
        push_variables(f"{self.global_id}.stdout", stdout)
        push_variables(f"{self.global_id}.stderr", stderr)
        push_variables(f"{self.global_id}.retcode", retcode)


class OutputStep(Step):
    """Output a message."""

    msg: str

    def init(self) -> None:
        """Initialize the step."""
        msg = self.raw_data.get("output", None)
        if msg is None:
            msg = self.raw_data.get("echo", None)

        self.msg = str(msg)

    def run(self) -> None:
        """Run the step."""
        call_ktrigger(IKernelTrigger.on_output, message=self.msg)


EchoStep = OutputStep


class MoveFileStep(Step):
    """Move a file."""

    src: Path
    dst: Path

    def init(self) -> None:
        """Initialize the step."""
        self.src = Path(self.raw_data.get("move", valtype=str))
        self.dst = Path(self.raw_data.get("to", valtype=str))

    def run(self) -> None:
        """Run the step."""
        call_ktrigger(IKernelTrigger.on_move_file, src=self.src, dst=self.dst)
        check_file_exists(self.dst)
        assert_rel_path(self.dst)
        shutil.move(self.src, self.dst)


class CopyFileStep(Step):
    """Copy files or directories."""

    srcs: list[str]
    dst: Path
    overwrite: bool
    keep_symlinks: bool
    excludes: list[str] | None

    def init(self) -> None:
        """Initialize the step."""
        srcs = self.raw_data.get("copy", valtype=str | list)
        self.dst = Path(self.raw_data.get("to", valtype=str))

        if isinstance(srcs, str):
            self.srcs = [srcs]
        else:
            assert_iter_types(
                srcs,
                str,
                RUValueError(_("The copy item must be a string.")),
            )
            self.srcs = srcs

        self.overwrite = self.raw_data.get("overwrite", True, valtype=bool)
        self.keep_symlinks = self.raw_data.get(
            "keep-symlinks",
            False,
            valtype=bool,
        )
        self.excludes = self.raw_data.get(
            "excludes",
            None,
            valtype=list | None,
        )

    def run(self) -> None:
        """Run the step."""
        if self.overwrite and self.dst.exists():
            rm_recursive(self.dst, strict=True)
        if self.dst.is_dir():
            check_file_exists(self.dst)
        assert_rel_path(self.dst)

        for src_glob in self.srcs:
            for src in glob.glob(src_glob):  # noqa: PTH207
                src_path = Path(src)
                call_ktrigger(
                    IKernelTrigger.on_copy,
                    src=src_path,
                    dst=self.dst,
                )
                copy_recursive(
                    src_path,
                    self.dst,
                    self.excludes,
                    strict=not self.overwrite,
                    symlinks=self.keep_symlinks,
                    exists_ok=self.overwrite,
                )


class RemoveStep(Step):
    """Remove a file or directory.

    This step is dangerous. Use it with caution!
    """

    globs: list[str]
    excludes: list[str]
    include_hidden: bool

    def init(self) -> None:
        """Initialize the step."""
        remove = self.raw_data.get("remove", valtype=str | list)
        if isinstance(remove, str):
            self.globs = [remove]
        else:
            assert_iter_types(
                remove,
                str,
                RUValueError(_("The remove item must be a string.")),
            )
            self.globs = remove

        self.include_hidden = self.raw_data.get(
            "include-hidden",
            False,
            valtype=bool,
        )
        self.excludes = self.raw_data.get("excludes", [], valtype=list)

    def run(self) -> None:
        """Run the step."""
        for glob_partten in self.globs:
            paths = glob.glob(  # pylint: disable=E1123  # noqa: PTH207
                glob_partten,
                recursive=True,
                include_hidden=self.include_hidden,
            )
            for str_path in paths:
                path = Path(str_path)
                call_ktrigger(IKernelTrigger.on_remove, path=path)
                rm_recursive(path, strict=True)


class ExtensionLoadStep(Step):
    """Load a Rubisco Excention manually."""

    path: Path

    def init(self) -> None:
        """Initialize the step."""
        self.path = Path(self.raw_data.get("extension", valtype=str))

    def run(self) -> None:
        """Run the step."""
        load_extension(self.path, WORKSPACE_ENV, strict=True)
        load_extension(self.path, USER_ENV, strict=True)
        load_extension(self.path, GLOBAL_ENV, strict=True)


class WorkflowRunStep(Step):
    """Run another workflow."""

    path: Path
    fail_fast: bool

    def init(self) -> None:
        """Initialize the step."""
        self.path = Path(self.raw_data.get("workflow", valtype=str))

        self.fail_fast = self.raw_data.get("fail-fast", True, valtype=bool)

    def run(self) -> None:
        """Run the step."""
        exc = run_workflow(self.path, fail_fast=self.fail_fast)
        if exc:
            push_variables(f"{self.global_id}.exception", exc)


class MklinkStep(Step):
    """Make a symbolic link."""

    src: Path
    dst: Path
    symlink: bool

    def init(self) -> None:
        """Initialize the step."""
        self.src = Path(self.raw_data.get("mklink", valtype=str))
        self.dst = Path(self.raw_data.get("to", valtype=str))

        self.symlink = self.raw_data.get("symlink", True, valtype=bool)

    def run(self) -> None:
        """Run the step."""
        call_ktrigger(
            IKernelTrigger.on_mklink,
            src=self.src,
            dst=self.dst,
            symlink=self.symlink,
        )

        assert_rel_path(self.dst)

        if self.symlink:
            os.symlink(self.src, self.dst)
        else:
            os.link(self.src, self.dst)


class CompressStep(Step):
    """Make a compressed archive."""

    src: Path
    dst: Path
    start: Path | None
    excludes: list[str] | None
    compress_format: str | None
    compress_level: int | None
    overwrite: bool

    def init(self) -> None:
        """Initialize the step."""
        self.src = Path(self.raw_data.get("compress", valtype=str))
        self.dst = Path(self.raw_data.get("to", valtype=str))
        _start = self.raw_data.get("start", None, valtype=str | None)
        self.start = Path(_start) if _start else None
        self.excludes = self.raw_data.get(
            "excludes",
            None,
            valtype=list | None,
        )
        self.compress_format = self.raw_data.get(
            "format",
            None,
            valtype=str | list | None,
        )
        self.compress_level = self.raw_data.get(
            "level",
            None,
            valtype=int | None,
        )
        self.overwrite = self.raw_data.get("overwrite", True, valtype=bool)

    def run(self) -> None:
        """Run the step."""
        if isinstance(self.compress_format, list):
            assert_iter_types(
                self.compress_format,
                str,
                RUValueError(
                    _("Compress format must be a list of string or a string."),
                ),
            )
            for fmt in self.compress_format:
                if fmt == "gzip":
                    ext = ".gz"
                elif fmt == "bzip2":
                    ext = ".bz2"
                elif fmt == "lzma":
                    ext = ".xz"
                elif fmt == "tgz":
                    ext = ".tar.gz"
                elif fmt == "tbz2":
                    ext = ".tar.bz2"
                elif fmt == "txz":
                    ext = ".tar.xz"
                else:
                    ext = f".{fmt}"

                dst = Path(str(self.dst) + ext)
                compress(
                    self.src,
                    dst,
                    self.start,
                    self.excludes,
                    fmt,
                    self.compress_level,
                    overwrite=self.overwrite,
                )
        else:
            compress(
                self.src,
                self.dst,
                self.start,
                self.excludes,
                self.compress_format,
                self.compress_level,
                overwrite=self.overwrite,
            )


class ExtractStep(Step):
    """Extract a compressed archive."""

    src: Path
    dst: Path
    compress_format: str | None
    overwrite: bool
    password: str | None

    def init(self) -> None:
        """Initialize the step."""
        self.src = Path(self.raw_data.get("extract", valtype=str))
        self.dst = Path(self.raw_data.get("to", valtype=str))
        self.compress_format = self.raw_data.get(
            "type",
            None,
            valtype=str | None,
        )
        self.overwrite = self.raw_data.get("overwrite", True, valtype=bool)
        self.password = self.raw_data.get("password", None, valtype=str | None)

    def run(self) -> None:
        """Run the step."""
        extract(
            self.src,
            self.dst,
            self.compress_format,
            self.password,
            overwrite=self.overwrite,
        )


step_types: dict[str, type[Step]] = {
    "shell": ShellExecStep,
    "mkdir": MkdirStep,
    "output": OutputStep,
    "echo": EchoStep,
    "popen": PopenStep,
    "move": MoveFileStep,
    "copy": CopyFileStep,
    "remove": RemoveStep,
    "load-extension": ExtensionLoadStep,
    "run-workflow": WorkflowRunStep,
    "mklink": MklinkStep,
    "compress": CompressStep,
    "extract": ExtractStep,
}

# Type is optional. If not provided, it will be inferred from the step data.
step_contributes: dict[type[Step], list[str]] = {
    ShellExecStep: ["run"],
    MkdirStep: ["mkdir"],
    PopenStep: ["popen"],
    OutputStep: ["output"],
    EchoStep: ["echo"],
    MoveFileStep: ["move", "to"],
    CopyFileStep: ["copy", "to"],
    RemoveStep: ["remove"],
    ExtensionLoadStep: ["extension"],
    WorkflowRunStep: ["workflow"],
    MklinkStep: ["mklink", "to"],
    CompressStep: ["compress", "to"],
    ExtractStep: ["extract", "to"],
}
