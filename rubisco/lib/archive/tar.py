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

"""Tar compress/extract utilities."""

import tarfile
from pathlib import Path

from rubisco.lib.archive.utils import get_includes, write_to_archive
from rubisco.lib.fileutil import check_file_exists, rm_recursive
from rubisco.lib.l10n import _
from rubisco.lib.variable import format_str
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

# pylint: disable=R0801

__all__ = ["compress_tarball", "extract_tarball"]


def extract_tarball(
    tarball: Path,
    dest: Path,
    compress_type: str | None = None,
    *,
    overwrite: bool = False,
) -> None:
    """Extract tarball to destination.

    Args:
        tarball (Path): Path to tarball.
        dest (Path): Destination directory.
        compress_type (str): Compression type. None means no compression.
            Default is None.
        overwrite (bool): Overwrite destination directory if it exists.

    Raises:
        AssertionError: If compress is not in ["gz", "bz2", "xz"]

    """
    compress_type = compress_type.lower().strip() if compress_type else None
    if compress_type == "gzip":
        compress_type = "gz"
    elif compress_type == "bzip2":
        compress_type = "bz2"
    if compress_type not in ["gz", "bz2", "xz", None]:
        raise AssertionError

    with tarfile.open(
        tarball,
        f"r:{compress_type}" if compress_type else "r",  # type: ignore[arg-type]
    ) as fp:
        fp: tarfile.TarFile
        memembers = fp.getmembers()
        if not overwrite:
            check_file_exists(dest)
        elif dest.exists():
            rm_recursive(dest)

        task_name = format_str(
            _(
                "Extracting '[underline]${{file}}[/underline]' to "
                "'[underline]${{path}}[/underline]' as '${{type}}' ...",
            ),
            fmt={
                "file": str(tarball),
                "path": str(dest),
                "type": f"tar.{compress_type}" if compress_type else "tar",
            },
        )
        call_ktrigger(
            IKernelTrigger.on_new_task,
            task_name=task_name,
            task_type=IKernelTrigger.TASK_EXTRACT,
            total=len(memembers),
        )

        for member in memembers:
            fp.extract(member, dest)
            call_ktrigger(
                IKernelTrigger.on_progress,
                task_name=task_name,
                current=1,
                delta=True,
                more_data={"path": Path(member.path), "dest": dest},
            )

        call_ktrigger(IKernelTrigger.on_finish_task, task_name=task_name)


def compress_tarball(  # pylint: disable=R0913, R0917 # noqa: PLR0913
    src: Path,
    dest: Path,
    start: Path | None = None,
    excludes: list[str] | None = None,
    compress_type: str | None = None,
    compress_level: int | None = None,
    *,
    overwrite: bool = False,
) -> None:
    """Compress a tarball to destination.

    Args:
        src (Path): Source file or directory.
        dest (Path): Destination tarball file.
        start (Path | None, optional): Start directory. Defaults to None.
        ```
            e.g.
                /
                ├── a
                │   ├── b
                │   │   ├── c
                If start is '/a', the tarball will be created as 'b/c'.
                If start is None, the tarball will be created as 'c'.
        ```
        excludes (list[str] | None, optional): List of excluded files.
            Supports glob patterns. Defaults to None.
        compress_type (str | None, optional): Compression type. It can be "gz",
            "bz2", "xz". Defaults to None.
        compress_level (int | None, optional): Compression level. It can be
            0 to 9. Defaults to None. Only for gzip and bzip2. Ignored for
            others.
        overwrite (bool, optional): Overwrite destination if it exists.
            Defaults to False.

    """
    compress_type = compress_type.lower().strip() if compress_type else None
    if compress_type == "gzip":
        compress_type = "gz"
    elif compress_type == "bzip2":
        compress_type = "bz2"
    if compress_type not in ["gz", "bz2", "xz", None]:
        raise AssertionError

    if not overwrite:
        check_file_exists(dest)
    elif dest.exists():
        rm_recursive(dest)
    task_name = format_str(
        _(
            "Compressing '[underline]${{path}}[/underline]' to "
            "'[underline]${{file}}[/underline]' as '${{type}}' ...",
        ),
        fmt={
            "path": str(src),
            "file": str(dest),
            "type": f"tar.{compress_type}" if compress_type else "tar",
        },
    )

    if not start:
        start = src.parent

    if compress_type in ["gz", "bz2"]:
        compress_level = compress_level if compress_level else 9
        fp = tarfile.open(  # noqa: SIM115
            dest,
            f"w:{compress_type}" if compress_type else "w",  # type: ignore[arg-type]
            compresslevel=compress_level,
        )
    else:
        fp = tarfile.open(  # noqa: SIM115
            dest,
            f"w:{compress_type}" if compress_type else "w",  # type: ignore[arg-type]
        )

    includes = get_includes(src, excludes)

    with fp:
        write_to_archive(
            includes,
            dest,
            start,
            lambda path, arcname: fp.add(
                path,
                arcname,
                recursive=False,
            ),
            task_name,
        )
