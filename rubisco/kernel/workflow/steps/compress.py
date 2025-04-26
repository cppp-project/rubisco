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

"""CompressStep implementation."""

from pathlib import Path

from rubisco.kernel.workflow.step import Step
from rubisco.lib.archive import compress
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.variable.utils import assert_iter_types

__all__ = ["CompressStep"]


class CompressStep(Step):
    """Make a compressed archive."""

    src: Path
    dst: Path
    start: Path | None
    excludes: list[str] | None
    compress_format: str | None
    compress_level: int | None
    overwrite: bool

    def init(self) -> None:
        """Initialize the step."""
        self.src = Path(self.raw_data.get("compress", valtype=str))
        self.dst = Path(self.raw_data.get("to", valtype=str))
        _start = self.raw_data.get("start", None, valtype=str | None)
        self.start = Path(_start) if _start else None
        self.excludes = self.raw_data.get(
            "excludes",
            None,
            valtype=list | None,
        )
        self.compress_format = self.raw_data.get(
            "format",
            None,
            valtype=str | list | None,
        )
        self.compress_level = self.raw_data.get(
            "level",
            None,
            valtype=int | None,
        )
        self.overwrite = self.raw_data.get("overwrite", True, valtype=bool)

    def run(self) -> None:
        """Run the step."""
        if isinstance(self.compress_format, list):
            assert_iter_types(
                self.compress_format,
                str,
                RUValueError(
                    _("Compress format must be a list of string or a string."),
                ),
            )
            for fmt in self.compress_format:
                if fmt == "gzip":
                    ext = ".gz"
                elif fmt == "bzip2":
                    ext = ".bz2"
                elif fmt == "lzma":
                    ext = ".xz"
                elif fmt == "tgz":
                    ext = ".tar.gz"
                elif fmt == "tbz2":
                    ext = ".tar.bz2"
                elif fmt == "txz":
                    ext = ".tar.xz"
                else:
                    ext = f".{fmt}"

                dst = Path(str(self.dst) + ext)
                compress(
                    self.src,
                    dst,
                    self.start,
                    self.excludes,
                    fmt,
                    self.compress_level,
                    overwrite=self.overwrite,
                )
        else:
            compress(
                self.src,
                self.dst,
                self.start,
                self.excludes,
                self.compress_format,
                self.compress_level,
                overwrite=self.overwrite,
            )
