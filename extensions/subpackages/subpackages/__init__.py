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

"""Rubisco subpackage manager."""

from pathlib import Path
from typing import Any, ClassVar

from rubisco.shared.api.cefs import (
    Argument,
    EventCallback,
    EventFileData,
    EventPath,
    Option,
    load_callback_args,
)
from rubisco.shared.api.exception import RUValueError
from rubisco.shared.api.kernel import Step
from rubisco.shared.api.l10n import _
from rubisco.shared.api.utils import find_command
from rubisco.shared.api.variable import fast_format_str
from rubisco.shared.extension import IRUExtension
from rubisco.shared.ktrigger import IKernelTrigger
from subpackages.package import Package
from subpackages.steps import FetchStep

__all__ = ["instance"]


def on_fetch(options: list[Option[Any]], args: list[Argument[Any]]) -> None:
    """Fetch git extension."""
    opts, _args = load_callback_args(options, args)
    protocol = opts.get("protocol", "http")
    shallow = opts.get("shallow", True)
    use_mirror = opts.get("use-mirror", True)
    if protocol not in {"http", "ssh"}:
        raise RUValueError(
            fast_format_str(
                _("Invalid protocol: ${{protocol}}"),
                fmt={"protocol": protocol},
            ),
            hint=_('We only support "http"(HTTP(s)) and "ssh"(SSH).'),
        )
    pkg = Package(Path.cwd())
    pkg.fetch(protocol=protocol, shallow=shallow, use_direct=not use_mirror)


class SubpackagesExtension(IRUExtension):
    """Rubisco subpackage manager."""

    ktrigger = IKernelTrigger()
    workflow_steps: ClassVar[dict[str, type[Step]]] = {
        "subpackages-fetch": FetchStep,
    }
    steps_contributions: ClassVar[dict[type[Step], list[str]]] = {
        FetchStep: ["subpkg-fetch"],
    }

    def extension_can_load_now(self) -> bool:
        """Load git extension."""
        return not (find_command("git") is None or not Path(".git").is_dir())

    def reqs_is_solved(self) -> bool:
        """Check for requirements are solved."""
        return True

    def on_load(self) -> None:
        """Load git extension."""
        EventPath("/fetch").mkfile(
            EventFileData(
                callbacks=[
                    EventCallback(
                        callback=on_fetch,
                        description=_("Fetch subpackages."),
                    ),
                ],
            ),
            options=[
                Option[str](
                    name="protocol",
                    title=_("Protocol"),
                    description=_("Protocol to use for fetching subpackages."),
                    typecheck=str,
                    aliases=["p"],
                    default="http",
                    ext_attributes={
                        "cli-advanced-options": [
                            {
                                "name": ["--http", "-H"],
                                "help": _(
                                    "Use HTTP(s) to fetch Git subpackages.",
                                ),
                                "action": "store_const",
                                "const": "http",
                            },
                            {
                                "name": ["--ssh", "-S"],
                                "help": _("Use SSH to fetch Git subpackages."),
                                "action": "store_const",
                                "const": "ssh",
                            },
                        ],
                    },
                ),
                Option[bool](
                    name="shallow",
                    title=_("Shallow"),
                    description=_("Use shallow clone."),
                    typecheck=bool,
                    default=True,
                    ext_attributes={
                        "cli-advanced-options": [
                            {
                                "name": "--no-shallow",
                                "help": _(
                                    "Do not use shallow mode to clone Git "
                                    "subpackages.",
                                ),
                                "action": "store_false",
                            },
                        ],
                    },
                ),
                Option[bool](
                    name="use-mirror",
                    title=_("Use Mirror"),
                    description=_(
                        "Enable mirror speedtest and auto selection.",
                    ),
                    typecheck=bool,
                    default=True,
                    ext_attributes={
                        "cli-advanced-options": [
                            {
                                "name": "-m",
                                "help": _(
                                    "Use mirror to fetch Git subpackages.",
                                ),
                                "action": "store_true",
                            },
                            {
                                "name": "-M",
                                "help": _(
                                    "Disable mirror speedtest and auto selection.",  # noqa: E501
                                ),
                                "action": "store_false",
                            },
                        ],
                    },
                ),
            ],
        )

    def solve_reqs(self) -> None:
        """Solve requirements."""


instance = SubpackagesExtension()
