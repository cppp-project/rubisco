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

"""RemoveStep implementation."""

import glob
from pathlib import Path

from rubisco.kernel.workflow.step import Step
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.fileutil import rm_recursive
from rubisco.lib.l10n import _
from rubisco.lib.variable.utils import assert_iter_types
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = ["RemoveStep"]


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
