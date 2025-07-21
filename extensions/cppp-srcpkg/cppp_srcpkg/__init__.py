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

"""Rubisco source package builder."""

from pathlib import Path
from typing import Any, ClassVar

from cppp_srcpkg.dist import dist
from rubisco.shared.api.cefs import (
    Argument,
    DynamicArguments,
    EventCallback,
    EventFileData,
    EventPath,
    Option,
    load_callback_args,
)
from rubisco.shared.api.kernel import Step, load_project_config
from rubisco.shared.api.l10n import _
from rubisco.shared.extension import IRUExtension
from rubisco.shared.ktrigger import IKernelTrigger


def on_dist(options: list[Option[Any]], args: list[Argument[Any]]) -> None:
    """Fetch git extension."""
    opts, args = load_callback_args(options, args)

    dest = Path(opts.get("destination", Path.cwd() / "dist"))
    src = Path(args[0].get()) if len(args) > 0 else Path.cwd()

    load_project_config(src)
    project_config = load_project_config(src)

    dist(src, dest, project_config)


class SrcpkgExtension(IRUExtension):
    """Rubisco source package builder extension."""

    ktrigger = IKernelTrigger()
    workflow_steps: ClassVar[dict[str, type[Step]]] = {}
    steps_contributions: ClassVar[dict[type[Step], list[str]]] = {}

    def extension_can_load_now(self) -> bool:
        """Load the extension."""
        return True

    def reqs_is_solved(self) -> bool:
        """Check for requirements are solved."""
        return True

    def on_load(self) -> None:
        """Load the extension."""
        EventPath("/srcdist").mkfile(
            EventFileData(
                args=DynamicArguments(
                    name="srcdir",
                    title=_("Source directory"),
                    description=_("Source directory."),
                    mincount=0,
                    maxcount=1,
                ),
                callbacks=[
                    EventCallback(
                        callback=on_dist,
                        description=_("Make source package."),
                    ),
                ],
            ),
            description=_("Make source package."),
            options=[
                Option[str](
                    name="destination",
                    title=_("Destination"),
                    typecheck=str,
                    aliases=["-d"],
                    description=_("Destination directory."),
                    default=str(Path.cwd() / "dist"),
                ),
            ],
        )

    def solve_reqs(self) -> None:
        """Solve requirements."""


instance = SrcpkgExtension()
