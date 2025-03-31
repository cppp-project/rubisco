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

from pathlib import Path
from typing import ClassVar

from git.exc import GitError
from git.repo import Repo
from rubisco.kernel.workflow import Step
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.fileutil import find_command
from rubisco.lib.l10n import _
from rubisco.lib.variable import format_str, push_variables
from rubisco.lib.version import Version
from rubisco.shared.extension import IRUExtension
from rubisco.shared.ktrigger import IKernelTrigger

__all__ = ["GitExtension"]


class GitExtension(IRUExtension):
    """Git extension."""

    name = "git"
    version = Version((0, 1, 0))
    ktrigger = IKernelTrigger()
    workflow_steps: ClassVar[dict[str, type[Step]]] = {}
    steps_contributions: ClassVar[dict[type[Step], list[str]]] = {}
    cur_repo: Repo

    def extension_can_load_now(self) -> bool:
        """Load git extension."""
        return not (find_command("git") is None or not Path(".git").is_dir())

    def reqs_is_sloved(self) -> bool:
        """Check for requirements are solved."""
        return True

    def on_load(self) -> None:
        """Load git extension."""
        try:
            self.cur_repo = Repo(Path.cwd())
        except GitError as exc:
            raise RUValueError(
                format_str(
                    _(
                        "Failed to load git repository [underline]${{path}}"
                        "[/underline]: ${{exc}}",
                    ),
                    fmt={
                        "path": str(Path.cwd()),
                        "exc": f"{type(exc).__name__}: {exc}",
                    },
                ),
            ) from exc

    def solve_reqs(self) -> None:
        """Solve requirements."""


instance = GitExtension()
