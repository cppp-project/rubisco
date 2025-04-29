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

from pathlib import Path

import json5 as json
import yaml

from rubisco.config import DEFAULT_CHARSET
from rubisco.kernel.workflow._interfaces import workflow_set_runner
from rubisco.kernel.workflow.steps import step_contributes, step_types
from rubisco.kernel.workflow.workflow import Workflow
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.variable import AutoFormatDict, make_pretty
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = ["register_step_type", "run_inline_workflow", "run_workflow"]


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
            message=fast_format_str(
                _(
                    "Step type '${{name}}' registered multiple times. "
                    "This may cause unexpected behavior. It's unsafe.",
                ),
                fmt={"name": name},
            ),
        )
    step_types[name] = cls
    if cls not in step_contributes:
        step_contributes[cls] = contributes
    logger.info(
        "Step type %s registered with contributes %s",
        name,
        contributes,
    )


def run_inline_workflow(
    data: AutoFormatDict | list[AutoFormatDict],
    *,
    fail_fast: bool = True,
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
            message=fast_format_str(
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
    *,
    fail_fast: bool = True,
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
                fast_format_str(
                    _(
                        "The suffix of ${{path}} is invalid.",
                    ),
                    fmt={"path": make_pretty(file.absolute())},
                ),
                hint=_("We only support '.json', '.json5', '.yaml', '.yml'."),
            )

        return run_inline_workflow(
            AutoFormatDict(workflow),
            fail_fast=fail_fast,
        )


workflow_set_runner(run_workflow)


if __name__ == "__main__":
    run_workflow(Path("workflow.yaml"))
