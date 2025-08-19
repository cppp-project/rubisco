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

"""Rubisco changelog generator."""

from pathlib import Path
from typing import ClassVar

from rubisco.shared.api.kernel import Step
from rubisco.shared.api.l10n import load_locale_domain
from rubisco.shared.extension import IRUExtension
from rubisco.shared.ktrigger import IKernelTrigger

from changelog.config import EXTENSION_NAME, LOCALE_DIR_NAME
from changelog.events import mount_to_cefs
from changelog.steps import ChangelogStep

__all__ = ["instance"]


class ChangelogExtension(IRUExtension):
    """Rubisco changelog generator."""

    ktrigger = IKernelTrigger()
    workflow_steps: ClassVar[dict[str, type[Step]]] = {
        "changelog": ChangelogStep,
    }
    steps_contributions: ClassVar[dict[type[Step], list[str]]] = {
        ChangelogStep: ["changelog"],
    }

    def extension_can_load_now(self) -> bool:
        """Load the extension."""
        return Path(".git").is_dir()

    def reqs_is_solved(self) -> bool:
        """Check for requirements are solved."""
        return True

    def on_load(self) -> None:
        """Load git extension."""
        load_locale_domain(self.resdir / LOCALE_DIR_NAME, EXTENSION_NAME)
        mount_to_cefs()

    def solve_reqs(self) -> None:
        """Solve requirements."""


instance = ChangelogExtension()
