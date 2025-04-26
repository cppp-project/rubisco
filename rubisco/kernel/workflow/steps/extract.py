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

"""ExtractStep implementation."""

from pathlib import Path

from rubisco.kernel.workflow.step import Step
from rubisco.lib.archive import extract

__all__ = ["ExtractStep"]


class ExtractStep(Step):
    """Extract a compressed archive."""

    src: Path
    dst: Path
    compress_format: str | None
    overwrite: bool
    password: str | None

    def init(self) -> None:
        """Initialize the step."""
        self.src = Path(self.raw_data.get("extract", valtype=str))
        self.dst = Path(self.raw_data.get("to", valtype=str))
        self.compress_format = self.raw_data.get(
            "type",
            None,
            valtype=str | None,
        )
        self.overwrite = self.raw_data.get("overwrite", True, valtype=bool)
        self.password = self.raw_data.get("password", None, valtype=str | None)

    def run(self) -> None:
        """Run the step."""
        extract(
            self.src,
            self.dst,
            self.compress_format,
            self.password,
            overwrite=self.overwrite,
        )
