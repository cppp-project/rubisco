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

"""Package class."""

from pathlib import Path

from rubisco.kernel.project_config import (
    ProjectConfigration,
    load_project_config,
)
from rubisco.lib.exceptions import RUNotRubiscoProjectError
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.variable.utils import make_pretty


class Package:
    """Package class."""

    name: str
    path: Path
    config: ProjectConfigration
    subpackages: list["Package"]

    def __init__(self, path: Path) -> None:
        """Parse a rubisco package.

        Args:
            path (Path): The path of the package.

        """
        try:
            self.config = load_project_config(path)
        except RUNotRubiscoProjectError as exc:
            raise RUNotRubiscoProjectError(
                fast_format_str(
                    _(
                        "Working directory '[underline]${{path}}[/underline]'"
                        " not a rubisco project.",
                    ),
                    fmt={"path": make_pretty(Path.cwd().absolute())},
                ),
                hint=fast_format_str(
                    _("'[underline]${{path}}[/underline]' is not found."),
                    fmt={"path": make_pretty(USER_REPO_CONFIG.absolute())},
                ),
            ) from exc
