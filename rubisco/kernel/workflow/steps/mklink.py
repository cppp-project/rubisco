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

"""MklinkStep implementation."""

import os
from pathlib import Path

from rubisco.kernel.workflow.step import Step
from rubisco.lib.fileutil import assert_rel_path
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = ["MklinkStep"]


class MklinkStep(Step):
    """Make a symbolic link."""

    src: Path
    dst: Path
    symlink: bool

    def init(self) -> None:
        """Initialize the step."""
        self.src = Path(self.raw_data.get("mklink", valtype=str))
        self.dst = Path(self.raw_data.get("to", valtype=str))

        self.symlink = self.raw_data.get("symlink", True, valtype=bool)

    def run(self) -> None:
        """Run the step."""
        call_ktrigger(
            IKernelTrigger.on_mklink,
            src=self.src,
            dst=self.dst,
            symlink=self.symlink,
        )

        assert_rel_path(self.dst)

        if self.symlink:
            os.symlink(self.src, self.dst)
        else:
            os.link(self.src, self.dst)
