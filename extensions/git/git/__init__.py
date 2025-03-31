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

"""C++ Plus Rubisco Git extension."""

from typing import ClassVar

from rubisco.kernel.workflow import Step
from rubisco.lib.version import Version
from rubisco.shared.extension import IRUExtension
from rubisco.shared.ktrigger import IKernelTrigger
from rubisco.lib.fileutil import find_command

__all__ = ["GitExtension"]


class GitExtension(IRUExtension):
    """Git extension."""

    name = "git"
    version = Version((0, 1, 0))
    ktrigger = IKernelTrigger()
    workflow_steps: ClassVar[dict[str, type[Step]]] = {}
    steps_contributions: ClassVar[dict[type[Step], list[str]]] = {}

    def extension_can_load_now(self) -> bool:
        """Load git extension."""
        return True

    def reqs_is_sloved(self) -> bool:
        """Check for requirements are solved."""
        return True

    def on_load(self) -> None:
        """Load git extension."""
        print("=== GIT LOADING ===")

    def solve_reqs(self) -> None:
        """Solve requirements."""

instance = GitExtension()
