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

"""ExtensionLoadStep implementation."""

from pathlib import Path

from rubisco.envutils.env import GLOBAL_ENV, USER_ENV, WORKSPACE_ENV
from rubisco.kernel.workflow._interfaces import load_extension
from rubisco.kernel.workflow.step import Step

__all__ = ["ExtensionLoadStep"]


class ExtensionLoadStep(Step):
    """Load a Rubisco Excention manually."""

    path: Path

    def init(self) -> None:
        """Initialize the step."""
        self.path = Path(self.raw_data.get("extension", valtype=str))

    def run(self) -> None:
        """Run the step."""
        load_extension(self.path, WORKSPACE_ENV, strict=True)
        load_extension(self.path, USER_ENV, strict=True)
        load_extension(self.path, GLOBAL_ENV, strict=True)
