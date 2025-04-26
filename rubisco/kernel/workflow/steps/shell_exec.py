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

"""ShellExecStep implementation."""

from pathlib import Path

from rubisco.kernel.workflow.step import Step
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.process import Process
from rubisco.lib.variable.utils import assert_iter_types
from rubisco.lib.variable.variable import push_variables

__all__ = ["ShellExecStep"]


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
