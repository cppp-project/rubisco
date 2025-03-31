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

"""Utilities for archive."""


from collections.abc import Callable
from pathlib import Path

from rubisco.lib.exceptions import RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.variable import format_str
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = ["get_includes", "write_to_archive"]


def get_includes(
    src: Path,
    excludes: list[str] | None = None,
) -> list[Path]:
    """Get included files list with includes and excludes.

    Args:
        src (Path): Source file or directory.
        excludes (list[str] | None, optional): List of excluded files.
            Defaults to None.

    Returns:
        list[Path]: Included files list.

    """
    _includes = src.rglob("*") if src.is_dir() else [src]
    includes: list[Path] = []
    for path in _includes:
        if excludes and any(path.match(ex) for ex in excludes):
            continue
        includes.append(path)
    return includes


def write_to_archive(
    includes: list[Path],
    dest: Path,
    start: Path,
    on_write: Callable[[Path, Path], None],
    task_name: str,
) -> None:
    """Write files to archive.

    Args:
        includes (list[Path]): Included files list.
        dest (Path): Destination archive file.
        start (Path | None, optional): Start directory. Defaults to None.
        on_write (Callable[[Path, Path], None]): Callback function to write
            file to archive. It takes two arguments: source file path and
            its arcname.
        task_name (str): Task for this compress/archive operation.

    """
    call_ktrigger(
        IKernelTrigger.on_new_task,
        task_name=task_name,
        task_type=IKernelTrigger.TASK_COMPRESS,
        total=len(includes),
    )
    for path in includes:
        try:
            arcname = path.relative_to(start)
        except ValueError as exc:
            raise RUValueError(
                format_str(
                    _(
                        "'[underline]${{path}}[/underline]' is not in the "
                        "subpath of '[underline]${{start}}[/underline]'",
                    ),
                    fmt={"path": str(path), "start": str(start)},
                ),
            ) from exc
        on_write(path, arcname)
        call_ktrigger(
            IKernelTrigger.on_progress,
            task_name=task_name,
            current=1,
            delta=True,
            more_data={"path": path, "dest": dest},
        )
    call_ktrigger(IKernelTrigger.on_finish_task, task_name=task_name)
