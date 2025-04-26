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

from rubisco.kernel.workflow.step import Step
from rubisco.kernel.workflow.steps.compress import CompressStep
from rubisco.kernel.workflow.steps.copyfile import CopyFileStep
from rubisco.kernel.workflow.steps.echo import EchoStep, OutputStep
from rubisco.kernel.workflow.steps.extensionload import ExtensionLoadStep
from rubisco.kernel.workflow.steps.extract import ExtractStep
from rubisco.kernel.workflow.steps.mkdir import MkdirStep
from rubisco.kernel.workflow.steps.mklink import MklinkStep
from rubisco.kernel.workflow.steps.movefile import MoveFileStep
from rubisco.kernel.workflow.steps.popen import PopenStep
from rubisco.kernel.workflow.steps.remove import RemoveStep
from rubisco.kernel.workflow.steps.shell_exec import ShellExecStep
from rubisco.kernel.workflow.steps.workflowrun import WorkflowRunStep

__all__ = ["step_contributes", "step_types"]


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
