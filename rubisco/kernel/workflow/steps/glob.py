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

"""CopyFileStep implementation."""

import glob
from pathlib import Path

from rubisco.kernel.workflow.step import Step
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.variable.utils import assert_iter_types
from rubisco.lib.variable.variable import push_variables
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = ["GlobFileStep"]


class GlobFileStep(Step):
    """Glob files or directories."""

    patterns: list[str]
    save_to: str | None
    root_dir: str | None
    recursive: bool
    include_hidden: bool

    def init(self) -> None:
        """Initialize the step."""
        patterns = self.raw_data.get("glob", valtype=str | list)

        if isinstance(patterns, str):
            self.patterns = [patterns]
        else:
            assert_iter_types(
                patterns,
                str,
                RUValueError(_("The copy item must be a string.")),
            )
            self.patterns = patterns

        self.root_dir = self.raw_data.get(
            "root",
            default=None,
            valtype=str | None,
        )
        self.save_to = self.raw_data.get(
            "save-to",
            default=None,
            valtype=str | None,
        )
        self.recursive = self.raw_data.get(
            "recursive",
            default=True,
            valtype=bool,
        )
        self.include_hidden = self.raw_data.get(
            "include-hidden",
            default=True,
            valtype=bool,
        )

    def run(self) -> None:
        """Run the step."""
        res: list[Path] = []
        for pattern in self.patterns:
            for src in glob.glob(  # noqa: PTH207
                pattern,
                root_dir=self.root_dir,
                recursive=self.recursive,
                include_hidden=self.include_hidden,
            ):
                src_path = Path(src)
                call_ktrigger(
                    IKernelTrigger.on_file_selected,
                    path=src_path,
                )
                res.append(src_path)
        if self.save_to:
            push_variables(self.save_to, res)
        push_variables(f"{self.global_id}.files", res)
