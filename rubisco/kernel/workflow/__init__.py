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

import uuid
from pathlib import Path
from typing import TYPE_CHECKING

import json5 as json
import yaml

from rubisco.config import DEFAULT_CHARSET
from rubisco.kernel.workflow._interfaces import workflow_set_runner
from rubisco.kernel.workflow.steps import step_contributes, step_types
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
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

    from rubisco.kernel.workflow.step import Step


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

        step_ids: list[str] = []

        for step_data in steps:
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

            step_cls = None

            if not step_type:
                for cls, contribute in step_contributes.items():
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
            self.raw_data.get("steps", valtype=list[dict[str, object]]),
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
                format_str(
                    _(
                        "The suffix of '[underline]${{path}}[/underline]' "
                        "is invalid.",
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
