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

"""MatrixStep implementation."""

import copy
import itertools
from collections.abc import Generator
from typing import Any

from rubisco.kernel.workflow._interfaces import WorkflowInterfaces
from rubisco.kernel.workflow.step import Step
from rubisco.lib.exceptions import RUTypeError
from rubisco.lib.l10n import _
from rubisco.lib.variable.autoformatdict import AutoFormatDict
from rubisco.lib.variable.autoformatlist import AutoFormatList
from rubisco.lib.variable.utils import assert_iter_types
from rubisco.lib.variable.var_contianer import VariableContainer
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = ["MatrixStep"]


def _generate_combinations(
    variables: dict[str, list[Any] | Any],
) -> Generator[AutoFormatDict]:
    names = list(variables.keys())
    values = list(variables.values())
    for idx, val in enumerate(values):
        if not isinstance(val, list):
            values[idx] = [val]

    for combination in itertools.product(*values):
        yield AutoFormatDict(zip(names, combination, strict=True))


def allocate_matrix_vars(
    mvars: dict[str, list[Any] | Any] | list[dict[str, Any]],
) -> AutoFormatList[AutoFormatDict]:
    """Allocate matrix vars.

    Args:
        mvars (dict[str, list[Any] | Any] | list[dict[str, Any]]): The
            matrix variables. If it is a list, each element must be a dict.
            Otherwise, it is a dict.

    Returns:
        list[dict[str, Any]]: The allocated matrix vars. If the input is a
            list , return the same list. Otherwise, return the independent
            assortment of the matrix vars.

    Raises:
        RUTypeError: If the input is not a list[dict[str, Any]] or a
        dict[str, list[Any] | Any].

    """
    if not mvars:
        return AutoFormatList([])

    if isinstance(mvars, list):
        assert_iter_types(
            mvars,
            dict,
            RUTypeError(_("Matrix variables must be a dict.")),
        )
        return AutoFormatList([AutoFormatDict(v) for v in mvars])

    return AutoFormatList(_generate_combinations(mvars))


def _in(var: AutoFormatDict, exclude: AutoFormatDict) -> bool:
    for key, value in exclude.items():
        if key not in var:
            return False
        if var[key] != value:
            return False
    return True


def exclude_matrix_vars(
    mvars: AutoFormatList[AutoFormatDict],
    excludes: dict[str, list[Any] | Any] | list[dict[str, Any]],
) -> AutoFormatList[AutoFormatDict]:
    """Exclude matrix vars.

    Args:
        mvars (AutoFormatList[AutoFormatDict]): The matrix vars.
        excludes (dict[str, list[Any] | Any] | list[dict[str, Any]]): The
            excludes. If it is a list, each element must be a dict.
            Otherwise, it is a dict.

    Returns:
        AutoFormatList[AutoFormatDict]: The excluded matrix vars.

    Raises:
        RUTypeError: If the input is not a list[dict[str, Any]] or a
        dict[str, list[Any] | Any].

    """
    if not excludes:
        return mvars

    excludes_list = allocate_matrix_vars(excludes)

    return AutoFormatList(
        [
            mvar
            for mvar in mvars
            if not any(_in(mvar, exclude) for exclude in excludes_list)
        ],
    )


class MatrixStep(Step):
    """Matrix step."""

    matrix_vars: dict[str, list[Any] | Any] | list[dict[str, Any]]
    excludes: dict[str, list[Any] | Any] | list[dict[str, Any]]
    steps: list[AutoFormatDict]

    def init(self) -> None:
        """Initialize the step."""
        self.matrix_vars = self.raw_data.get("matrix", valtype=list | dict)
        self.excludes = AutoFormatList(
            self.raw_data.get("excludes", [], valtype=list | dict),
        )
        self.steps = list(self.raw_data.get("steps", valtype=list))

    def run(self) -> None:
        """Run the step."""
        matrix_vars = allocate_matrix_vars(self.matrix_vars)
        matrix_vars = exclude_matrix_vars(matrix_vars, self.excludes)

        for idx, mvars in enumerate(matrix_vars):
            with VariableContainer(mvars):
                call_ktrigger(IKernelTrigger.pre_run_matrix, variables=mvars)
                default_id = f"{self.id}.matrix.{idx}"
                WorkflowInterfaces.get_run_inline_workflow()(
                    copy.deepcopy(self.steps),  # What the fuck?
                    default_id,
                )
                call_ktrigger(IKernelTrigger.post_run_matrix, variables=mvars)
