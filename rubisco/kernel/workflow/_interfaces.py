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

"""Interfaces for workflow module.

To avoid circular import, we use the protocol to define the interface.
"""


from pathlib import Path
from typing import Protocol, runtime_checkable

from rubisco.envutils.env import RUEnvironment
from rubisco.envutils.packages import ExtensionPackageInfo

__all__ = ["load_extension", "run_workflow"]


def load_extension(
    ext: Path | str | ExtensionPackageInfo,
    env: RUEnvironment,
    *,
    strict: bool = False,
) -> None:
    """Load the extension.

    Args:
        ext (Path | str | ExtensionPackageInfo):If it is a str, it will be
            treat as extension's name, the extension will be loaded from the
            default extension directory. If the path is a path, the extension
            will be loaded from the path. If the path is ExtensionPackageInfo
            type, the extension will be loaded from the package info.
        env (RUEnvironment): The environment of the extension.
            It will be used only if the extension is a installed extension.
            If the extension is a standalone extension, it will be ignored.
            We will get the extension's info from the `rubisco.json` file.
        strict (bool, optional): If True, raise an exception if the extension
            loading failed.

    """
    raise NotImplementedError


@runtime_checkable
class _LoadExtensionFunction(Protocol):  # pylint: disable=R0903
    def __call__(
        self,
        ext: Path | str | ExtensionPackageInfo,
        env: RUEnvironment,
        *,
        strict: bool = False,
    ) -> None: ...


def workflow_set_extloader(
    extloader: _LoadExtensionFunction,
) -> None:
    """Set the extension loader. For internal use only.

    Args:
        extloader (_LoadExtensionFunction): The extension loader.

    """
    global load_extension  # pylint: disable=global-statement # noqa: PLW0603

    load_extension = extloader


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
    raise NotImplementedError


@runtime_checkable
class _RunWorkflowFunction(Protocol):  # pylint: disable=R0903
    def __call__(
        self,
        file: Path,
        *,
        fail_fast: bool = True,
    ) -> Exception | None: ...


def workflow_set_runner(runner: _RunWorkflowFunction) -> None:
    """Set the workflow runner. For internal use only.

    Args:
        runner (_RunWorkflowFunction): The workflow runner.

    """
    global run_workflow  # pylint: disable=global-statement # noqa: PLW0603
    run_workflow = runner
