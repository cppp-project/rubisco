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
from shutil import copyfile

from cppp_srcpkg.ignore import Manifest
from rubisco.shared.api.kernel import (
    ProjectConfigration,
    is_rubisco_project,
    load_project_config,
)
from rubisco.shared.api.l10n import _
from rubisco.shared.api.utils import human_readable_size
from rubisco.shared.api.variable import fast_format_str
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger


def _dist(
    srcdir: Path,
    dstdir: Path,
    task_name: str,
    copied_size: int,
    manifest: Manifest,
) -> int:
    files = srcdir.iterdir()
    if not files:
        # We don't allow empty directory.
        return 0

    dstdir.mkdir(parents=True, exist_ok=True)
    for file in files:
        if file.resolve() == dstdir.resolve():
            # Skip self. Destination may be the children of source dir.
            continue
        relpath = file.relative_to(srcdir)
        if manifest.need_ignore(file):
            continue
        if is_rubisco_project(file):
            config = load_project_config(file)
            dist(file, dstdir / relpath, config)
        elif file.is_dir():
            copied_size = _dist(
                file,
                dstdir / relpath,
                task_name,
                copied_size,
                manifest,
            )
        else:
            filepath = dstdir / relpath
            # Keep symlink info.
            copyfile(file, filepath, follow_symlinks=True)
            if file.is_file():
                copied_size += file.stat().st_size
            call_ktrigger(
                IKernelTrigger.on_progress,
                task_name=task_name,
                current=1.0,
                delta=True,
                status_msg=human_readable_size(copied_size),
            )
    return copied_size


def dist(srcdir: Path, dstdir: Path, project: ProjectConfigration) -> None:
    """Dist source package.

    Args:
        srcdir (Path): Source directory.
        dstdir (Path): Destination directory.
        project (ProjectConfigration): Project configuration.

    """
    manifest = Manifest(srcdir)

    call_ktrigger(
        IKernelTrigger.on_new_task,
        task_start_msg=fast_format_str(
            _(
                "Making source package for project: [cyan]${{name}}[/cyan] ...",
            ),
            fmt={"name": project.name},
        ),
        task_name=project.name,
        total=-1,
    )
    _dist(srcdir, dstdir, project.name, 0, manifest)
    call_ktrigger(
        IKernelTrigger.on_finish_task,
        task_name=project.name,
    )
