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

"""CopyFileStep implementation."""

import glob
from pathlib import Path

from rubisco.kernel.workflow.step import Step
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.fileutil import (
    assert_rel_path,
    check_file_exists,
    copy_recursive,
    rm_recursive,
)
from rubisco.lib.l10n import _
from rubisco.lib.variable.utils import assert_iter_types
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = ["CopyFileStep"]


class CopyFileStep(Step):
    """Copy files or directories."""

    srcs: list[str]
    dst: Path
    overwrite: bool
    keep_symlinks: bool
    excludes: list[str] | None

    def init(self) -> None:
        """Initialize the step."""
        srcs = self.raw_data.get("copy", valtype=str | list)
        self.dst = Path(self.raw_data.get("to", valtype=str))

        if isinstance(srcs, str):
            self.srcs = [srcs]
        else:
            assert_iter_types(
                srcs,
                str,
                RUValueError(_("The copy item must be a string.")),
            )
            self.srcs = srcs

        self.overwrite = self.raw_data.get("overwrite", True, valtype=bool)
        self.keep_symlinks = self.raw_data.get(
            "keep-symlinks",
            False,
            valtype=bool,
        )
        self.excludes = self.raw_data.get(
            "excludes",
            None,
            valtype=list | None,
        )

    def run(self) -> None:
        """Run the step."""
        if self.overwrite and self.dst.exists():
            rm_recursive(self.dst, strict=True)
        if self.dst.is_dir():
            check_file_exists(self.dst)
        assert_rel_path(self.dst)

        for src_glob in self.srcs:
            for src in glob.glob(src_glob):  # noqa: PTH207
                src_path = Path(src)
                call_ktrigger(
                    IKernelTrigger.on_copy,
                    src=src_path,
                    dst=self.dst,
                )
                copy_recursive(
                    src_path,
                    self.dst,
                    self.excludes,
                    strict=not self.overwrite,
                    symlinks=self.keep_symlinks,
                    exists_ok=self.overwrite,
                )
