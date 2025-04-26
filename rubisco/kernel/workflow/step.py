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

"""Workflow step interface."""

from __future__ import annotations

import abc
from abc import abstractmethod
from typing import TYPE_CHECKING

from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.variable import AutoFormatDict, format_str, make_pretty
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

if TYPE_CHECKING:
    from rubisco.kernel.workflow import Workflow

__all__ = ["Step"]


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
            data (AutoFormatDict[str, str | int | bool]): The step json data.
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
