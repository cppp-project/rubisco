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

"""Workflow support.

Workflow is a ordered list of steps. Each step only contains one action.
"""

from __future__ import annotations

import abc
import glob
import os
import shutil
import uuid
from abc import abstractmethod
from typing import TYPE_CHECKING, Any

import json5 as json
import yaml

from rubisco.config import DEFAULT_CHARSET
from rubisco.lib.archive import compress, extract
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.fileutil import (
    check_file_exists,
    copy_recursive,
    rm_recursive,
)
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.pathlib import Path
from rubisco.lib.process import Process
from rubisco.lib.variable import (
    AutoFormatDict,
    assert_iter_types,
    format_str,
    make_pretty,
    pop_variables,
    push_variables,
)
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

if TYPE_CHECKING:
    from collections.abc import Generator

__all__ = [
    "CompressStep",
    "CopyFileStep",
    "EchoStep",
    "ExtentionLoadStep",
    "ExtractStep",
    "MkdirStep",
    "MklinkStep",
    "MoveFileStep",
    "OutputStep",
    "PopenStep",
    "RemoveStep",
    "ShellExecStep",
    "Step",
    "Workflow",
    "WorkflowRunStep",
    "_set_extloader",
    "register_step_type",
    "run_inline_workflow",
    "run_workflow",
]


def load_extension(*args: Any, **kwargs: Any) -> None:  # noqa: ANN401
    """Not implemented. Use `_set_extloader` to set.

    Args:
        *args: The arguments.
        **kwargs: The keyword arguments.

    Raises:
        NotImplementedError: Always.

    """
    raise NotImplementedError


# Avoid circular import.
def _set_extloader(extloader) -> None:  # noqa: ANN001
    global load_extension  # pylint: disable=global-statement # noqa: PLW0603

    load_extension = extloader


class Step(abc.ABC):  # pylint: disable=too-many-instance-attributes
    """A step in the workflow."""

    id: str
    parent_workflow: Workflow
    name: str
    next: Step | None
    raw_data: AutoFormatDict
    global_id: str
    strict: bool
    suc: bool

    def __init__(
        self,
        data: AutoFormatDict,
        parent_workflow: Workflow,
    ) -> None:
        """Create a new step.

        Args:
            data (AutoFormatDict): The step json data.
            parent_workflow (Workflow): The parent workflow.

        """
        self.suc = False

        self.parent_workflow = parent_workflow
        self.raw_data = data
        self.name = data.get("name", "", valtype=str)
        self.strict = data.get("strict", True, valtype=bool)
        self.next = None
        self.id = data.get("id", valtype=str)  # Always exists.
        self.global_id = f"{self.parent_workflow.id}.{self.id}"

        self.init()

        call_ktrigger(
            IKernelTrigger.pre_run_workflow_step,
            step=self,
        )

        try:
            self.run()
        except Exception as exc:  # pylint: disable=broad-except # noqa: BLE001
            if self.strict:
                raise exc from None
            logger.warning("Step %s failed.", self.name, exc_info=True)
            call_ktrigger(
                IKernelTrigger.on_error,
                message=format_str(
                    _("Step '${{step}}' failed: ${{exc}}"),
                    fmt={
                        "step": make_pretty(self.name, _("<Unnamed>")),
                        "exc": f"{type(exc).__name__}: {exc}",
                    },
                ),
            )

        self.suc = True

    def __str__(self) -> str:
        """Return the name of the step.

        Returns:
            str: The name of the step.

        """
        return self.name

    def __repr__(self) -> str:
        """Return the representation of the step.

        Returns:
            str: The repr of the step.

        """
        return f"<{self.__class__.__name__} {self.name}>"

    @abstractmethod
    def init(self) -> None:
        """Initialize the step."""

    @abstractmethod
    def run(self) -> None:
        """Run the step."""


# Built-in step types.
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
        retcode = Process(self.cmd, self.cwd).run(self.fail_on_error)
        push_variables(f"{self.global_id}.retcode", retcode)


class MkdirStep(Step):
    """Make directories."""

    paths: list[Path]

    def init(self) -> None:
        """Initialize the step."""
        paths = self.raw_data.get("mkdir", valtype=str | list)
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
            self.stdout,
            self.stderr,
            self.fail_on_error,
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
        call_ktrigger(IKernelTrigger.on_output, msg=self.msg)


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
                    not self.overwrite,
                    self.keep_symlinks,
                    self.overwrite,
                    self.excludes,
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


class ExtentionLoadStep(Step):
    """Load a Rubisco Excention manually."""

    path: Path

    def init(self) -> None:
        """Initialize the step."""
        self.path = Path(self.raw_data.get("extension", valtype=str))

    def run(self) -> None:
        """Run the step."""
        load_extension(self.path, strict=True)


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
        exc = run_workflow(self.path, self.fail_fast)
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
                    self.overwrite,
                )
        else:
            compress(
                self.src,
                self.dst,
                self.start,
                self.excludes,
                self.compress_format,
                self.compress_level,
                self.overwrite,
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
            self.overwrite,
            self.password,
        )


step_types = {
    "shell": ShellExecStep,
    "mkdir": MkdirStep,
    "output": OutputStep,
    "echo": EchoStep,
    "popen": PopenStep,
    "move": MoveFileStep,
    "copy": CopyFileStep,
    "remove": RemoveStep,
    "load-extension": ExtentionLoadStep,
    "run-workflow": WorkflowRunStep,
    "mklink": MklinkStep,
    "compress": CompressStep,
    "extract": ExtractStep,
}

# Type is optional. If not provided, it will be inferred from the step data.
step_contribute = {
    ShellExecStep: ["run"],
    MkdirStep: ["mkdir"],
    PopenStep: ["popen"],
    OutputStep: ["output"],
    EchoStep: ["echo"],
    MoveFileStep: ["move", "to"],
    CopyFileStep: ["copy", "to"],
    RemoveStep: ["remove"],
    ExtentionLoadStep: ["extension"],
    WorkflowRunStep: ["workflow"],
    MklinkStep: ["mklink", "to"],
    CompressStep: ["compress", "to"],
    ExtractStep: ["extract", "to"],
}


class Workflow:
    """A workflow."""

    id: str
    name: str
    first_step: Step | None
    raw_data: AutoFormatDict

    pushed_variables: list[str]

    def __init__(self, data: AutoFormatDict) -> None:
        """Create a new workflow.

        Args:
            data (AutoFormatDict): The workflow json data.

        """
        self.pushed_variables = []
        pairs = data.get("vars", [], valtype=list)
        for pair in pairs:
            assert_iter_types(
                pairs,
                dict,
                RUValueError(
                    _("Workflow variables must be a list of name and value."),
                ),
            )
            for key, val in pair.items():
                self.pushed_variables.append(str(key))
                push_variables(str(key), val)

        self.id = data.get(
            "id",
            str(uuid.uuid4()),
            valtype=str,
        )
        self.name = data.get("name", valtype=str)
        self.raw_data = data

    def _parse_steps(  # noqa: C901
        self,
        steps: list[AutoFormatDict],
    ) -> Step | None:
        """Parse the steps.

        Args:
            steps (list[AutoFormatDict]): The steps dict data.

        Returns:
            Step: The first step.

        """
        first_step = None
        prev_step = None

        step_ids = []

        for step_data in steps:
            if not isinstance(step_data, dict):
                raise RUValueError(_("A workflow step must be a dict."))
            step_id = step_data.get(
                "id",
                str(uuid.uuid4()),
                valtype=str,
            )
            step_name = step_data.get("name", "", valtype=str)
            step_type = step_data.get("type", "", valtype=str)
            step_cls: type | None

            step_data["id"] = step_id
            if step_id in step_ids:
                raise RUValueError(
                    format_str(
                        _("Step id '${{step_id}}' is duplicated."),
                        fmt={"step_id": make_pretty(step_id)},
                    ),
                )
            step_ids.append(step_id)

            if not step_type:
                for cls, contribute in step_contribute.items():
                    is_match = all(
                        step_data.get(contribute_item, None) is not None
                        for contribute_item in contribute  # All items exist.
                    )
                    if is_match:
                        step_cls = cls
                        break
            else:
                step_cls = step_types.get(step_type)
                if step_cls is None:
                    raise RUValueError(
                        format_str(
                            _(
                                "Unknown step type: '${{step_type}}' of step "
                                "'${{step_name}}'. Please check the workflow.",
                            ),
                            fmt={
                                "step_type": make_pretty(step_type),
                                "step_name": make_pretty(step_name),
                            },
                        ),
                        hint=_(
                            "Consider use 'type' attribute manually.",
                        ),
                    )

            if step_cls is None:
                raise RUValueError(
                    format_str(
                        _(
                            "The type of step '${{step}}'[black](${{step_id}})"
                            "[/black] in workflow '${{workflow}}'[black]("
                            "${{workflow_id}})[/black] is not provided and "
                            "could not be inferred.",
                        ),
                        fmt={
                            "step": make_pretty(step_name, _("<Unnamed>")),
                            "workflow": make_pretty(self.name, _("<Unnamed>")),
                            "step_id": step_id,
                            "workflow_id": self.id,
                        },
                    ),
                )
            step = step_cls(step_data, self)
            if step.suc:
                call_ktrigger(
                    IKernelTrigger.post_run_workflow_step,
                    step=step,
                )

            if prev_step is not None:
                prev_step.next = step

            if first_step is None:
                first_step = step

            prev_step = step

        return first_step

    def __str__(self) -> str:
        """Return the name of the workflow.

        Returns:
            str: The name of the workflow.

        """
        return self.name

    def __repr__(self) -> str:
        """Return the representation of the workflow.

        Returns:
            str: The repr of the workflow.

        """
        return f"<{self.__class__.__name__} {self.name}>"

    def __iter__(self) -> Generator[Step, None, None]:
        """Iterate over the steps.

        Yields:
            Step: One step.

        """
        cur_step = self.first_step
        while cur_step is not None:
            yield cur_step
            cur_step = cur_step.next

    def run(self) -> None:
        """Run the workflow."""
        call_ktrigger(
            IKernelTrigger.pre_run_workflow,
            workflow=self,
        )
        self.first_step = self._parse_steps(
            self.raw_data.get("steps", valtype=list),
        )
        call_ktrigger(
            IKernelTrigger.post_run_workflow,
            workflow=self,
        )

    def __del__(self) -> None:
        """Pop variables."""
        for name in self.pushed_variables:
            pop_variables(name)


def register_step_type(name: str, cls: type, contributes: list[str]) -> None:
    """Register a step type.

    Args:
        name (str): The name of the step type.
        cls (type): The class of the step type.
        contributes (list[str]): The contributes of the step type.

    """
    if name in step_types:
        call_ktrigger(
            IKernelTrigger.on_warning,
            message=format_str(
                _(
                    "Step type '${{name}}' registered multiple times. "
                    "This may cause unexpected behavior. It's unsafe.",
                ),
                fmt={"name": make_pretty(name)},
            ),
        )
    step_types[name] = cls
    if cls not in step_contribute:
        step_contribute[cls] = contributes
    logger.info(
        "Step type %s registered with contributes %s",
        name,
        contributes,
    )


def run_inline_workflow(
    data: AutoFormatDict | list[AutoFormatDict],
    fail_fast: bool = True,  # noqa: FBT001 FBT002
) -> Exception | None:
    """Run a inline workflow.

    Args:
        data (AutoFormatDict | list[AutoFormatDict]): Workflow data.
        fail_fast (bool, optional): Raise an exception if run failed.
            Defaults to True.

    Returns:
        Exception | None: If running failed without fail-fast, return its
            exception. Return None if succeed.

    """
    if isinstance(data, list):
        data = AutoFormatDict({"name": _("<Inline Workflow>"), "steps": data})

    wf = Workflow(data)
    try:
        wf.run()
    except Exception as exc:  # pylint: disable=broad-except # noqa: BLE001
        if fail_fast:
            raise exc from None
        call_ktrigger(
            IKernelTrigger.on_warning,
            message=format_str(
                _(
                    "Workflow running failed: ${{exc}}",
                ),
                fmt={"exc": f"{type(exc).__name__}: {exc}"},
            ),
        )
        return exc
    return None


def run_workflow(
    file: Path,
    fail_fast: bool = True,  # noqa: FBT001 FBT002
) -> Exception | None:
    """Run a workflow file.

    Args:
        file (Path): Workflow file path. It can be a JSON, or a yaml.
        fail_fast (bool, optional): Raise an exception if run failed.

    Raises:
        RUValueError: If workflow's step parse failed.

    Returns:
        Exception | None: If running failed without fail-fast, return its
            exception. Return None if succeed.

    """
    with file.open(encoding=DEFAULT_CHARSET) as f:
        if file.suffix.lower() in [".json", ".json5"]:
            workflow = json.load(f)
        elif file.suffix.lower() in [".yaml", ".yml"]:
            workflow = yaml.safe_load(f)
        else:
            raise RUValueError(
                format_str(
                    _(
                        "The suffix of '[underline]${{path}}[/underline]' "
                        "is invalid.",
                    ),
                    fmt={"path": make_pretty(file.absolute())},
                ),
                hint=_("We only support '.json', '.json5', '.yaml', '.yml'."),
            )

        return run_inline_workflow(AutoFormatDict(workflow), fail_fast)


if __name__ == "__main__":
    run_workflow(Path("workflow.yaml"))
