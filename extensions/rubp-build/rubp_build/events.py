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

"""Rubisco binary package builder command events."""

from pathlib import Path
from typing import Any

from rubisco.shared.api.cefs import (
    Argument,
    DynamicArguments,
    EventCallback,
    EventFileData,
    EventPath,
    Option,
    load_callback_args,
)
from rubisco.shared.api.kernel import load_project_config
from rubisco.shared.api.l10n import _
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

from rubp_build.metadata import RUBPMatadata

__all__ = ["mount_to_cefs"]


def on_metadata(options: list[Option[Any]], args: list[Argument[Any]]) -> None:
    """Output metadata."""
    _opts, args_ = load_callback_args(options, args)
    project_dir = Path.cwd() if len(args_) == 0 else Path(args_[0])
    config = load_project_config(project_dir).config
    metadata = RUBPMatadata.from_json(config)
    call_ktrigger(IKernelTrigger.on_output, message=metadata.to_dict())


def mount_to_cefs() -> None:
    """Mount cefs events."""
    EventPath("/rubp").mkdir(
        description=_(
            "Rubisco binary package builder. (Build RuBP from event is not"
            "supported. Please use workflow to build RuBP.)",
        ),
    )
    EventPath("/rubp/metadata").mkfile(
        data=EventFileData(
            args=DynamicArguments(
                name="srcdir",
                title=_("Project directory"),
                description=_("Project directory path."),
                mincount=0,
                maxcount=1,
            ),
            callbacks=[
                EventCallback(
                    callback=on_metadata,
                    description=_("Get RuBP metadata."),
                ),
            ],
        ),
        description=_("Get RuBP metadata."),
    )
