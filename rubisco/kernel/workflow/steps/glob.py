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
from rubisco.lib.l10n import _
from rubisco.lib.variable.utils import assert_iter_types
from rubisco.lib.variable.variable import push_variables
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = ["GlobFileStep"]


class GlobFileStep(Step):  # pylint: disable=R0902
    """Glob files or directories."""

    patterns: list[str]
    exclude_patterns: list[str]
    save_to: str | None
    root_dir: str | None
    recursive: bool
    include_hidden: bool
    include_regular_files: bool
    include_directories: bool
    include_symlinks: bool
    include_hardlinks: bool
    include_fifos: bool
    include_sockets: bool
    include_block_devices: bool
    include_char_devices: bool
    include_mountpoints: bool

    def init(self) -> None:
        """Initialize the step."""
        patterns = self.raw_data.get("glob", valtype=str | list)
        exclude_patterns = self.raw_data.get("excludes", [], valtype=str | list)

        if isinstance(patterns, str):
            self.patterns = [patterns]
        else:
            assert_iter_types(
                patterns,
                str,
                RUValueError(_("The glob item must be a string.")),
            )
            self.patterns = patterns

        if isinstance(exclude_patterns, str):
            self.exclude_patterns = [exclude_patterns]
        else:
            assert_iter_types(
                exclude_patterns,
                str,
                RUValueError(_("The glob item must be a string.")),
            )
            self.exclude_patterns = exclude_patterns

        self.root_dir = self.raw_data.get(
            "root",
            default=None,
            valtype=str | None,
        )
        self.save_to = self.raw_data.get(
            "save-to",
            default=None,
            valtype=str | None,
        )
        self.recursive = self.raw_data.get(
            "recursive",
            default=True,
            valtype=bool,
        )
        self.include_hidden = self.raw_data.get(
            "include-hidden",
            default=True,
            valtype=bool,
        )
        self.include_regular_files = self.raw_data.get(
            "regular",
            default=True,
            valtype=bool,
        )
        self.include_directories = self.raw_data.get(
            "dirs",
            default=True,
            valtype=bool,
        )
        self.include_symlinks = self.raw_data.get(
            "symlinks",
            default=True,
            valtype=bool,
        )
        self.include_hardlinks = self.raw_data.get(
            "hardlinks",
            default=True,
            valtype=bool,
        )
        self.include_fifos = self.raw_data.get(
            "fifos",
            default=True,
            valtype=bool,
        )
        self.include_sockets = self.raw_data.get(
            "sockets",
            default=True,
            valtype=bool,
        )
        self.include_block_devices = self.raw_data.get(
            "block-devices",
            default=True,
            valtype=bool,
        )
        self.include_char_devices = self.raw_data.get(
            "char-devices",
            default=True,
            valtype=bool,
        )
        devices = self.raw_data.get(
            "devices",
            default=True,
            valtype=bool,
        )
        if devices:
            self.include_block_devices = True
            self.include_char_devices = True
        self.include_mountpoints = self.raw_data.get(
            "mountpoints",
            default=True,
            valtype=bool,
        )

    def _need_ignore(self, path: Path) -> bool:
        return not (
            (self.include_regular_files and path.is_file())
            or (self.include_directories and path.is_dir())
            or (self.include_symlinks and path.is_symlink())
            or (self.include_hardlinks and path.stat().st_nlink > 1)
            or (self.include_fifos and path.is_fifo())
            or (self.include_sockets and path.is_socket())
            or (self.include_block_devices and path.is_block_device())
            or (self.include_char_devices and path.is_char_device())
            or (self.include_mountpoints and path.is_mount())
        )

    def run(self) -> None:
        """Run the step."""
        selected: list[Path] = []
        for pattern in self.patterns:
            selected.extend([
                Path(src).absolute()
                for src in glob.glob(  # noqa: PTH207
                    pattern,
                    root_dir=self.root_dir,
                    recursive=self.recursive,
                    include_hidden=self.include_hidden,
                )
            ])
        excludes: list[Path] = []
        for pattern in self.exclude_patterns:
            excludes.extend(
                [
                    Path(src).absolute()
                    for src in glob.glob(  # noqa: PTH207
                        pattern,
                        root_dir=self.root_dir,
                        recursive=self.recursive,
                        include_hidden=self.include_hidden,
                    )
                ],
            )
        res: list[Path] = []
        res.extend(
            [
                p
                for p in selected
                if p.absolute() not in excludes and not self._need_ignore(p)
            ],
        )
        for path in res:
            call_ktrigger(
                IKernelTrigger.on_file_selected,
                path=path,
            )
        if self.save_to:
            push_variables(self.save_to, res)
        push_variables(f"{self.global_id}.files", res)
