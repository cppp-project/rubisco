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

"""Workflow implementation."""

from collections.abc import Generator
from typing import Any

from rubisco.kernel.workflow.step import Step
from rubisco.kernel.workflow.steps import step_contributes, step_types
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.variable.autoformatdict import AutoFormatDict
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.variable.utils import make_pretty
from rubisco.lib.variable.variable import pop_variables, push_variables
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = ["Workflow"]


class Workflow:
    """A workflow."""

    id: str
    name: str
    first_step: Step | None
    raw_data: AutoFormatDict

    pushed_variables: list[str]

    def __init__(self, data: AutoFormatDict, default_id: str) -> None:
        """Create a new workflow.

        Args:
            data (AutoFormatDict): The workflow json data.
            default_id (str): The default id of the workflow.

        """
        self.pushed_variables = []
        pairs = data.get("vars", {}, valtype=dict[str, Any])

        for key, val in pairs.items():
            self.pushed_variables.append(str(key))
            push_variables(str(key), val)

        self.id = data.get(
            "id",
            default_id,
            valtype=str,
        )
        self.name = data.get("name", valtype=str)
        self.raw_data = data

    def _parse_steps(  # noqa: C901
        self,
        steps: list[AutoFormatDict],
    ) -> Step | None:
        """Parse the steps and run them.

        Args:
            steps (list[AutoFormatDict]): The steps dict data.

        Returns:
            Step: The first step.

        """
        first_step = None
        prev_step = None

        step_ids: list[str] = []

        for step_idx, step_data in enumerate(steps):
            step_id = step_data.get(
                "id",
                f"{self.id}.steps.{step_idx}",
                valtype=str,
            )
            step_name = step_data.get("name", "", valtype=str)
            step_type = step_data.get("type", "", valtype=str)
            step_cls: type | None

            step_data["id"] = step_id
            if step_id in step_ids:
                raise RUValueError(
                    fast_format_str(
                        _("Step id '${{step_id}}' is duplicated."),
                        fmt={"step_id": step_id},
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
                    # Contribute must be non-empty or ignored.
                    if is_match and contribute:
                        step_cls = cls
                        break
            else:
                step_cls = step_types.get(step_type)
                if step_cls is None:
                    raise RUValueError(
                        fast_format_str(
                            _(
                                "Unknown step type: '${{step_type}}' of step "
                                "'${{step_name}}'. Please check the workflow.",
                            ),
                            fmt={
                                "step_type": step_type,
                                "step_name": step_name,
                            },
                        ),
                        hint=_(
                            "Consider use 'type' attribute manually.",
                        ),
                    )

            if step_cls is None:
                raise RUValueError(
                    fast_format_str(
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
