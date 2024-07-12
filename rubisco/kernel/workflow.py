# -*- coding: utf-8 -*-
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

"""
Workflow support.
Workflow is a ordered list of steps. Each step only contains one action.
"""

import glob
import os
import shutil
import sys
import uuid
from pathlib import Path

import json5 as json
import yaml

from rubisco.config import DEFAULT_CHARSET
from rubisco.lib.archive import compress, extract
from rubisco.lib.exceptions import RUValueException
from rubisco.lib.fileutil import (check_file_exists, copy_recursive,
                                  rm_recursive)
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.process import Process, popen
from rubisco.lib.variable import (AutoFormatDict, assert_iter_types,
                                  format_str, make_pretty, pop_variables,
                                  push_variables)
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = [
    "Step",
    "ShellExecStep",
    "MkdirStep",
    "PopenStep",
    "OutputStep",
    "EchoStep",
    "MoveFileStep",
    "CopyFileStep",
    "RemoveStep",
    "ExtentionLoadStep",
    "WorkflowRunStep",
    "MklinkStep",
    "CompressStep",
    "ExtractStep",
    "Workflow",
    "register_step_type",
    "run_inline_workflow",
    "run_workflow",
    "_set_extloader",
]

try:  # Avoid circular import.
    from rubisco.shared.extention import load_extention
except ImportError:
    load_extention = NotImplemented


def _set_extloader(extloader):  # Avoid circular import.
    global load_extention  # pylint: disable=global-statement

    load_extention = extloader


class Step:
    """A step in the workflow."""

    id: str
    par_workflow: "Workflow"
    name: str
    desc: str
    next: "Step | None"
    raw_data: AutoFormatDict
    global_id: str

    def __init__(self, data: AutoFormatDict, par_workflow: "Workflow"):
        """Create a new step.

        Args:
            data (AutoFormatDict): The step json data.
            par_workflow (Workflow): The parent workflow.
        """

        self.par_workflow = par_workflow
        self.raw_data = data
        self.name = data.get("name", "", valtype=str)
        self.desc = data.get("desc", "", valtype=str)
        self.next = None
        self.id = data.get("id", valtype=str)  # Always exists.
        self.global_id = f"{self.par_workflow.id}.{self.id}"

        call_ktrigger(
            IKernelTrigger.pre_run_workflow_step,
            step=self,
        )

    def __str__(self):
        """Return the name of the step.

        Returns:
            str: The name of the step.
        """

        return self.name

    def __repr__(self):
        """Return the representation of the step.

        Returns:
            str: The repr of the step.
        """

        return f"<{self.__class__.__name__} {self.name}>"


# Built-in step types.
class ShellExecStep(Step):  # pylint: disable=too-few-public-methods
    """A shell execution step."""

    cmd: str
    cwd: Path
    fail_on_error: bool

    def __init__(self, data: AutoFormatDict, par_workflow: "Workflow"):
        self.cmd = data.get("run", valtype=str | list)
        if isinstance(self.cmd, list):
            assert_iter_types(
                self.cmd,
                str,
                RUValueException(
                    _("The shell command list must be a list of strings.")
                ),
            )

        self.cwd = Path(data.get("cwd", "", valtype=str))
        self.fail_on_error = data.get(
            "fail-on-error",
            True,
            valtype=bool,
        )
        super().__init__(data, par_workflow)

        retcode = Process(self.cmd, self.cwd).run(self.fail_on_error)
        push_variables(f"{self.global_id}.retcode", retcode)


class MkdirStep(Step):  # pylint: disable=too-few-public-methods
    """Make directories."""

    paths: list[Path]

    def __init__(self, data: AutoFormatDict, par_workflow: "Workflow"):
        paths = data.get("mkdir", valtype=str | list)
        if isinstance(paths, list):
            assert_iter_types(
                paths,
                str,
                RUValueException(
                    _(
                        "The paths must be a list of strings.",
                    )
                ),
            )
            self.paths = [Path(path) for path in paths]
        else:
            self.paths = [Path(paths)]
        super().__init__(data, par_workflow)

        for path in self.paths:
            call_ktrigger(IKernelTrigger.on_mkdir, path=path)
            os.makedirs(path, exist_ok=True)


class PopenStep(Step):  # pylint: disable=too-few-public-methods
    """A popen step."""

    cmd: str
    cwd: Path
    fail_on_error: bool
    stdout: bool
    stderr: int

    def __init__(self, data: AutoFormatDict, par_workflow: "Workflow"):
        self.cmd = data.get("popen", valtype=str)

        self.cwd = Path(data.get("cwd", "", valtype=str))
        self.fail_on_error = data.get(
            "fail-on-error",
            True,
            valtype=bool,
        )
        self.stdout = data.get("stdout", True, valtype=bool)
        stderr_mode = data.get("stderr", True, valtype=bool | str)
        if stderr_mode is True:
            self.stderr = 1
        elif stderr_mode is False:
            self.stderr = 0
        else:
            self.stderr = 2

        super().__init__(data, par_workflow)

        stdout, stderr, retcode = popen(
            self.cmd, self.cwd, self.stdout, self.stderr, self.fail_on_error
        )
        push_variables(f"{self.global_id}.stdout", stdout)
        push_variables(f"{self.global_id}.stderr", stderr)
        push_variables(f"{self.global_id}.retcode", retcode)


class OutputStep(Step):  # pylint: disable=too-few-public-methods
    """Output a message."""

    msg: str

    def __init__(self, data: AutoFormatDict, par_workflow: "Workflow"):
        msg = data.get("output", None)
        if msg is None:
            msg = data.get("echo", None)

        self.msg = str(msg)

        super().__init__(data, par_workflow)

        call_ktrigger(IKernelTrigger.on_output, msg=self.msg)


EchoStep = OutputStep


class MoveFileStep(Step):  # pylint: disable=too-few-public-methods
    """Move a file."""

    src: Path
    dst: Path

    def __init__(self, data: AutoFormatDict, par_workflow: "Workflow"):
        self.src = Path(data.get("move", valtype=str))
        self.dst = Path(data.get("to", valtype=str))

        super().__init__(data, par_workflow)

        call_ktrigger(IKernelTrigger.on_move_file, src=self.src, dst=self.dst)
        check_file_exists(self.dst)
        shutil.move(self.src, self.dst)


class CopyFileStep(Step):  # pylint: disable=too-few-public-methods
    """Copy files or directories."""

    srcs: Path
    dst: Path
    overwrite: bool
    keep_symlinks: bool
    excludes: list[str] | None

    def __init__(self, data: AutoFormatDict, par_workflow: "Workflow"):
        srcs = data.get("copy", valtype=str | list)
        self.dst = Path(data.get("to", valtype=str))

        if isinstance(srcs, str):
            self.srcs = [Path(srcs)]
        else:
            assert_iter_types(
                srcs,
                str,
                RUValueException(_("The copy item must be a string.")),
            )
            self.srcs = [Path(src) for src in srcs]

        self.overwrite = data.get("overwrite", True, valtype=bool)
        self.keep_symlinks = data.get(
            "keep-symlinks",
            False,
            valtype=bool,
        )
        self.excludes = data.get(
            "excludes",
            None,
            valtype=list | None,
        )

        super().__init__(data, par_workflow)

        if self.overwrite and self.dst.exists():
            rm_recursive(self.dst, strict=True)
        if self.dst.is_dir():
            check_file_exists(self.dst)

        for src_glob in self.srcs:
            for src in glob.glob(str(src_glob)):
                src = Path(src)
                call_ktrigger(IKernelTrigger.on_copy, src=src, dst=self.dst)
                copy_recursive(
                    src,
                    self.dst,
                    not self.overwrite,
                    self.keep_symlinks,
                    self.overwrite,
                    self.excludes,
                )


class RemoveStep(Step):  # pylint: disable=too-few-public-methods
    """
    Remove a file or directory.
    This step is dangerous. Use it with caution!
    """

    globs: list[str]
    excludes: list[str]
    strict: bool
    include_hidden: bool

    def __init__(self, data: AutoFormatDict, par_workflow: "Workflow"):
        remove = data.get("remove", valtype=str | list)
        if isinstance(remove, str):
            self.globs = [remove]
        else:
            assert_iter_types(
                remove,
                str,
                RUValueException(_("The remove item must be a string.")),
            )
            self.globs = remove

        self.strict = data.get("strict", True, valtype=bool)
        self.include_hidden = data.get(
            "include-hidden",
            False,
            valtype=bool,
        )
        self.excludes = data.get("excludes", [], valtype=list)

        super().__init__(data, par_workflow)

        for glob_partten in self.globs:
            if sys.version_info >= (3, 10):
                paths = glob.glob(  # pylint: disable=unexpected-keyword-arg
                    glob_partten,
                    recursive=True,
                    include_hidden=self.include_hidden,
                )
            else:
                paths = glob.glob(
                    glob_partten,
                    recursive=True,
                )
            for path in paths:
                path = Path(path)
                call_ktrigger(IKernelTrigger.on_remove, path=path)
                rm_recursive(path, self.strict)


class ExtentionLoadStep(Step):  # pylint: disable=too-few-public-methods
    """
    Load a Rubisco Excention manually.
    """

    path: Path
    strict: bool

    def __init__(self, data: AutoFormatDict, par_workflow: "Workflow"):
        self.path = Path(data.get("extention", valtype=str))

        self.strict = data.get("strict", True, valtype=bool)

        super().__init__(data, par_workflow)

        load_extention(self.path, self.strict, is_auto=False)


class WorkflowRunStep(Step):  # pylint: disable=too-few-public-methods
    """
    Run another workflow.
    """

    path: Path
    fail_fast: bool

    def __init__(self, data: AutoFormatDict, par_workflow: "Workflow"):
        self.path = Path(data.get("workflow", valtype=str))

        self.fail_fast = data.get("fail-fast", True, valtype=bool)

        super().__init__(data, par_workflow)

        exc = run_workflow(self.path, self.fail_fast)
        if exc:
            push_variables(f"{self.global_id}.exception", exc)


class MklinkStep(Step):  # pylint: disable=too-few-public-methods
    """
    Make a symbolic link.
    """

    src: Path
    dst: Path
    strict: bool
    symlink: bool

    def __init__(self, data: AutoFormatDict, par_workflow: "Workflow"):
        self.src = Path(data.get("mklink", valtype=str))
        self.dst = Path(data.get("to", valtype=str))

        self.strict = data.get("strict", True, valtype=bool)
        self.symlink = data.get("symlink", True, valtype=bool)

        super().__init__(data, par_workflow)

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


class CompressStep(Step):  # pylint: disable=too-few-public-methods
    """
    Make a compressed archive.
    """

    src: Path
    dst: Path
    start: Path | None
    excludes: list[str] | None
    compress_format: str | None
    compress_level: int | None
    overwrite: bool

    def __init__(self, data: AutoFormatDict, par_workflow: "Workflow"):
        self.src = Path(data.get("compress", valtype=str))
        self.dst = Path(data.get("to", valtype=str))
        _start = data.get("start", None, valtype=str | None)
        self.start = Path(_start) if _start else None
        self.excludes = data.get("excludes", None, valtype=list | None)
        self.compress_format = data.get(
            "format",
            None,
            valtype=str | list | None,
        )
        self.compress_level = data.get(
            "level",
            None,
            valtype=int | None,
        )
        self.overwrite = data.get("overwrite", True, valtype=bool)

        super().__init__(data, par_workflow)

        if isinstance(self.compress_format, list):
            assert_iter_types(
                self.compress_format,
                str,
                RUValueException(
                    _("Compress format must be a list of string or a string.")
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


class ExtractStep(Step):  # pylint: disable=too-few-public-methods
    """
    Extract a compressed archive.
    """

    src: Path
    dst: Path
    compress_format: str | None
    overwrite: bool
    password: str | None

    def __init__(self, data: AutoFormatDict, par_workflow: "Workflow"):
        self.src = Path(data.get("extract", valtype=str))
        self.dst = Path(data.get("to", valtype=str))
        self.compress_format = data.get(
            "type",
            None,
            valtype=str | None,
        )
        self.overwrite = data.get("overwrite", True, valtype=bool)
        self.password = data.get("password", None, valtype=str | None)

        super().__init__(data, par_workflow)

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
    "load-extention": ExtentionLoadStep,
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
    ExtentionLoadStep: ["extention"],
    WorkflowRunStep: ["workflow"],
    MklinkStep: ["mklink", "to"],
    CompressStep: ["compress", "to"],
    ExtractStep: ["extract", "to"],
}


class Workflow:
    """A workflow."""

    id: str
    name: str
    first_step: Step
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
                RUValueException(
                    _("Workflow variables must be a list of name and value.")
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

    def _parse_steps(self, steps: list[AutoFormatDict]) -> None:
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
                raise RUValueException(_("A workflow step must be a dict."))
            step_id = step_data.get(
                "id",
                str(uuid.uuid4()),
                valtype=str,
            )
            step_name = step_data.get("name", "", valtype=str)
            step_type = step_data.get("type", "", valtype=str)
            step_cls: type = None

            step_data["id"] = step_id
            if step_id in step_ids:
                raise RUValueException(
                    format_str(
                        _("Step id '${{step_id}}' is duplicated."),
                        fmt={"step_id": make_pretty(step_id)},
                    )
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
                step_cls = step_types.get(step_type, None)
                if step_cls is None:
                    raise RUValueException(
                        format_str(
                            _(
                                "Unknown step type: '${{step_type}}' of step "
                                "'${{step_name}}'. Please check the workflow."
                            ),
                            fmt={
                                "step_type": make_pretty(step_type),
                                "step_name": make_pretty(step_name),
                            },
                        ),
                        hint=_(
                            "Please check typo or use 'type' attribute manually.",  # noqa: E501
                        ),
                    )

            if step_cls is None:
                raise RUValueException(
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
                    )
                )
            step = step_cls(step_data, self)
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

    def __str__(self):
        """Return the name of the workflow.

        Returns:
            str: The name of the workflow.
        """
        return self.name

    def __repr__(self):
        """Return the representation of the workflow.

        Returns:
            str: The repr of the workflow.
        """
        return f"<{self.__class__.__name__} {self.name}>"

    def __iter__(self):
        """Iterate over the steps.

        Yields:
            Step: One step.
        """

        cur_step = self.first_step
        while cur_step is not None:
            yield cur_step
            cur_step = cur_step.next

    def run(self):
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

    def __del__(self):
        """
        Pop variables.
        """

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
                    "Step type '${{name}}' registered multiple times. It's unsafe.",  # noqa: E501
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
    data: AutoFormatDict | list[AutoFormatDict], fail_fast: bool = True
) -> Exception | None:
    """Run a inline workflow

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
    except Exception as exc:  # pylint: disable=broad-exception-caught
        if fail_fast:
            raise exc from None
        call_ktrigger(
            IKernelTrigger.on_warning,
            message=format_str(
                _(
                    "Workflow running failed: ${{exc}}",
                ),
                fmt={"exc": f"{type(exc).__name__}: {str(exc)}"},
            ),
        )
        return exc
    return None


def run_workflow(file: Path, fail_fast: bool = True) -> Exception | None:
    """Run a workflow file.

    Args:
        file (Path): Workflow file path. It can be a JSON, or a yaml.
        fail_fast (bool, optional): Raise an exception if run failed.

    Raises:
        RUValueException: If workflow's step parse failed.

    Returns:
        Exception | None: If running failed without fail-fast, return its
            exception. Return None if succeed.
    """

    with open(file, encoding=DEFAULT_CHARSET) as f:
        if file.suffix.lower() in [".json", ".json5"]:
            workflow = json.load(f)
        elif file.suffix.lower() in [".yaml", ".yml"]:
            workflow = yaml.safe_load(f)
        else:
            raise RUValueException(
                format_str(
                    _(
                        "The suffix of '[underline]${{path}}[/underline]' "
                        "is invalid."
                    ),
                    fmt={"path": make_pretty(file.absolute())},
                ),
                hint=_("We only support '.json', '.json5', '.yaml', '.yml'."),
            )

        return run_inline_workflow(AutoFormatDict(workflow), fail_fast)


if __name__ == "__main__":
    import rich

    rich.print(f"{__file__}: {__doc__.strip()}")

    run_workflow("workflow.yaml")
