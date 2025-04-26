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

"""MoveFileStep implementation."""

import shutil
from pathlib import Path

from rubisco.kernel.workflow.step import Step
from rubisco.lib.fileutil import assert_rel_path, check_file_exists
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = ["MoveFileStep"]


class MoveFileStep(Step):
    """Move a file."""

    src: Path
    dst: Path

    def init(self) -> None:
        """Initialize the step."""
        self.src = Path(self.raw_data.get("move", valtype=str))
        self.dst = Path(self.raw_data.get("to", valtype=str))

    def run(self) -> None:
        """Run the step."""
        call_ktrigger(IKernelTrigger.on_move_file, src=self.src, dst=self.dst)
        check_file_exists(self.dst)
        assert_rel_path(self.dst)
        shutil.move(self.src, self.dst)
