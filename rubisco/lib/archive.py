# -*- coding: utf-8 -*-
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

"""
Archive compression/extraction utilities.
"""

import bz2
import gzip
import lzma
import os
import tarfile
import time
import zipfile
from pathlib import Path

import py7zr
import py7zr.callbacks
import py7zr.exceptions

from rubisco.config import COPY_BUFSIZE, DEFAULT_CHARSET
from rubisco.lib.exceptions import RUValueException
from rubisco.lib.fileutil import check_file_exists, rm_recursive
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.variable import format_str
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = ["compress", "extract"]


def extract_tarball(
    tarball: Path,
    dest: Path,
    compress_type: str | None = None,
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
        f"r:{compress_type}" if compress_type else "r",
    ) as fp:
        memembers = fp.getmembers()
        if not overwrite:
            check_file_exists(dest)
        elif dest.exists():
            rm_recursive(dest)
        task_name = format_str(
            _(
                "Extracting '[underline]${{file}}[/underline]' to "
                "'[underline]${{path}}[/underline]' as '${{type}}' ..."
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


def extract_zip(
    file: Path,
    dest: Path,
    overwrite: bool = False,
    password: str | None = None,
) -> None:
    """Extract zip file to destination.

    Args:
        file (Path): Path to zip file.
        dest (Path): Destination directory.
        overwrite (bool): Overwrite destination directory if it exists.
        password (str): Password to decrypt zip file. Default is None.
    """

    with zipfile.ZipFile(file, "r") as fp:
        memembers = fp.infolist()
        if not overwrite:
            check_file_exists(dest)
        elif dest.exists():
            rm_recursive(dest)
        task_name = format_str(
            _(
                "Extracting '[underline]${{file}}[/underline]' to "
                "'[underline]${{path}}[/underline]' as '${{type}}' ..."
            ),
            fmt={"file": str(file), "path": str(dest), "type": "zip"},
        )
        call_ktrigger(
            IKernelTrigger.on_new_task,
            task_name=task_name,
            task_type=IKernelTrigger.TASK_EXTRACT,
            total=len(memembers),
        )

        for member in memembers:
            fp.extract(
                member,
                dest,
                pwd=password.encode(DEFAULT_CHARSET) if password else None,
            )
            perm = member.external_attr >> 16
            if perm:
                os.chmod(dest / member.filename, perm)
            utime = member.date_time
            utime = time.mktime(utime + (0, 0, -1))
            print(dest / member.filename, (utime, utime))
            os.utime(dest / member.filename, (utime, utime))
            call_ktrigger(
                IKernelTrigger.on_progress,
                task_name=task_name,
                current=1,
                delta=True,
                more_data={"path": Path(member.filename), "dest": dest},
            )

        call_ktrigger(IKernelTrigger.on_finish_task, task_name=task_name)


def extract_7z(
    file: Path,
    dest: Path,
    password: str | None = None,
) -> None:
    """Extract 7z file to destination.

    Args:
        file (Path): Path to 7z file.
        dest (Path): Destination directory.
        password (str): Password to decrypt 7z file. Default is None.
    """

    with py7zr.SevenZipFile(file, mode="r", password=password) as fp:
        task_name = format_str(
            _(
                "Extracting '[underline]${{file}}[/underline]' to "
                "'[underline]${{path}}[/underline]' as '${{type}}' ..."
            ),
            fmt={"file": str(file), "path": str(dest), "type": "7z"},
        )

        class _ExtractCallback(py7zr.callbacks.ExtractCallback):
            end: bool = False

            def report_start_preparation(self):
                """
                Report a start of preparation event such as making list of
                    files and looking into its properties.
                """

                self.end = False
                call_ktrigger(
                    IKernelTrigger.on_new_task,
                    task_name=task_name,
                    task_type=IKernelTrigger.TASK_EXTRACT,
                    total=len(fp.getnames()),
                )

            def report_start(
                self,
                processing_file_path: str,
                processing_bytes: int,
            ):
                """
                Report a start event of specified archive file and its input
                    bytes.

                Args:
                    processing_file_path (str): Processing file path.
                    processing_bytes (int): Processing bytes.
                """

            def report_update(self, decompressed_bytes: int):
                """
                Report an event when large file is being extracted more than 1
                    second or when extraction is finished. Receives a number of
                    decompressed bytes since the last update.

                Args:
                    decompressed_bytes (int): Decompressed bytes.
                """

            def report_end(  # pylint: disable=unused-argument
                self,
                processing_file_path: str,
                wrote_bytes: int,
            ):
                """
                Report an end event of specified archive file and its output
                    bytes.

                Args:
                    processing_file_path (str): Processing file path.
                    wrote_bytes (int): Wrote bytes.
                """

                call_ktrigger(
                    IKernelTrigger.on_progress,
                    task_name=task_name,
                    current=1,
                    delta=True,
                    more_data={
                        "path": Path(processing_file_path),
                        "dest": dest,
                    },
                )

            def report_warning(self, message: str):
                """
                Report an warning event with its message.

                Args:
                    message (str): Warning message.
                """

                call_ktrigger(
                    IKernelTrigger.on_warning,
                    message=message,
                )

            def report_postprocess(self):
                """
                Report a start of post processing event such as set file
                    properties and permissions or creating symlinks.
                """

                call_ktrigger(
                    IKernelTrigger.on_finish_task,
                    task_name=task_name,
                )
                self.end = True

        callback = _ExtractCallback()
        fp.extractall(dest, callback=callback)

        # call_ktrigger(IKernelTrigger.on_finish_task, task_name=task_name)
        while not callback.end:
            try:
                fp.reporterd.join(0.01)
            except RuntimeError:
                pass


def extract_file(  # pylint: disable=too-many-branches
    file: Path,
    dest: Path,
    compress_type: str = "gz",
    overwrite: bool = False,
) -> None:
    """Extract a compressed data file to destination.
    This function only supports gzip, bzip2 and xz compression which are
    only supports one-file compression.

    Args:
        file (Path): Path to compressed file.
        dest (Path): Destination directory.
        compress_type (str): Compression type. Default is "gz".
        overwrite (bool): Overwrite destination directory if it exists.

    Raises:
        AssertionError: If compress is not in ["gz", "bz2", "xz"]
    """

    compress_type = compress_type.lower().strip()
    if compress_type == "gzip":
        compress_type = "gz"
    elif compress_type == "bzip2":
        compress_type = "bz2"
    if compress_type not in ["gz", "bz2", "xz"]:
        raise AssertionError

    if compress_type == "gz":
        fsrc = gzip.open(file, "rb")
    elif compress_type == "bz2":
        fsrc = bz2.BZ2File(file, "rb")
    elif compress_type == "xz":
        fsrc = lzma.open(file, "rb")
    else:
        raise AssertionError

    with fsrc:
        fsrc.seek(0, os.SEEK_END)
        fsize = fsrc.tell()
        fsrc.seek(0, os.SEEK_SET)
        if not overwrite:
            check_file_exists(dest)
        elif dest.exists():
            rm_recursive(dest)
        with open(dest, "wb") as fdst:
            if fsize > COPY_BUFSIZE * 50:
                task_name = format_str(
                    _(
                        "Extracting '[underline]${{file}}[/underline]'"
                        " to '[underline]${{path}}[/underline]'"
                        " as '${{type}}' ..."
                    ),
                    fmt={
                        "file": str(file),
                        "path": str(dest),
                        "type": compress_type,
                    },
                )
                call_ktrigger(
                    IKernelTrigger.on_new_task,
                    task_name=task_name,
                    task_type=IKernelTrigger.TASK_EXTRACT,
                    total=fsize,
                )
                while buf := fsrc.read(COPY_BUFSIZE):
                    call_ktrigger(
                        IKernelTrigger.on_progress,
                        task_name=task_name,
                        current=len(buf),
                        delta=True,
                    )
                    fdst.write(buf)
                call_ktrigger(
                    IKernelTrigger.on_finish_task,
                    task_name=task_name,
                )
            else:
                while buf := fsrc.read(COPY_BUFSIZE):
                    fdst.write(buf)


def extract(  # pylint: disable=too-many-branches
    file: Path,
    dest: Path,
    compress_type: str | None = None,
    overwrite: bool = False,
    password: str | None = None,
):
    """Extract compressed file to destination.

    Args:
        file (Path): Path to compressed file.
        dest (Path): Destination file or directory.
        compress_type (str | None, optional): Compression type. It can be "gz",
            "bz2", "xz", "zip", "7z", "tar.gz", "tar.bz2", "tar.xz" and "tar".
            Defaults to None.
        overwrite (bool, optional): Overwrite destination if it exists.
            Defaults to False.
        password (str | None, optional): Password to decrypt compressed file.
            Defaults to None. Tarball is not supported.
    """

    compress_type = compress_type.lower().strip() if compress_type else None
    try:
        if compress_type is None:
            suffix1 = file.suffix
            suffix2 = file.suffixes[-2] if len(file.suffixes) > 1 else None
            if suffix2 == ".tar":
                compress_type = "tar" + suffix1
            elif suffix1:
                compress_type = suffix1[1:]
            else:
                raise RUValueException(
                    format_str(
                        _(
                            "Unable to determine compression type of "
                            "'[underline]${{path}}[/underline]'"
                        ),
                        fmt={"path": str(file)},
                    ),
                    hint=_("Please specify the compression type explicitly."),
                )
        if compress_type in ["gz", "gzip"]:
            logger.info("Extracting '%s' to '%s' as 'gz' ...", file, dest)
            extract_file(file, dest, "gz", overwrite)
        elif compress_type in ["bz2", "bzip2"]:
            logger.info("Extracting '%s' to '%s' as 'bz2' ...", file, dest)
            extract_file(file, dest, "bz2", overwrite)
        elif compress_type in ["xz", "lzma"]:
            logger.info("Extracting '%s' to '%s' as 'xz' ...", file, dest)
            extract_file(file, dest, "xz", overwrite)
        elif compress_type == "zip":
            logger.info("Extracting '%s' to '%s' as 'zip' ...", file, dest)
            extract_zip(file, dest, overwrite, password)
        elif compress_type == "7z":
            logger.info("Extracting '%s' to '%s' as '7z' ...", file, dest)
            extract_7z(file, dest, password)
        elif compress_type in ["tar.gz", "tgz"]:
            logger.info("Extracting '%s' to '%s' as 'tar.gz' ...", file, dest)
            extract_tarball(file, dest, "gz", overwrite)
        elif compress_type in ["tar.bz2", "tbz2"]:
            logger.info("Extracting '%s' to '%s' as 'tar.bz2' ...", file, dest)
            extract_tarball(file, dest, "bz2", overwrite)
        elif compress_type in ["tar.xz", "txz"]:
            logger.info("Extracting '%s' to '%s' as 'tar.xz' ...", file, dest)
            extract_tarball(file, dest, "xz", overwrite)
        elif compress_type == "tar":
            logger.info("Extracting '%s' to '%s' as 'tar' ...", file, dest)
            extract_tarball(file, dest, None, overwrite)
        else:
            raise AssertionError
    except AssertionError:
        logger.error(
            "Unsupported compression type: '%s'",
            compress_type,
        )
        raise RUValueException(
            format_str(
                _("Unsupported compression type: '${{type}}'"),
                fmt={"type": compress_type},
            ),
            hint=_(
                "Supported types are 'gz', 'bz2', 'xz', 'zip', '7z', 'tar', "
                "'tar.gz', 'tar.bz2', 'tar.xz'. You can also use the 'tgz', "
                "'txz' and 'tbz2'."
            ),
        ) from None
    except (
        tarfile.TarError,
        zipfile.BadZipfile,
        zipfile.LargeZipFile,
        lzma.LZMAError,
        py7zr.exceptions.ArchiveError,
        OSError,
    ) as exc:
        logger.exception(
            "Failed to extract '%s' to '%s'.",
            file,
            dest,
        )
        raise RUValueException(
            format_str(
                _("Failed to extract '${{file}}' to '${{dest}}': '${{exc}}'"),
                fmt={"file": file, "dest": dest, "exc": str(exc)},
            )
        ) from exc


def compress_tarball(  # pylint: disable=too-many-arguments
    src: Path,
    dest: Path,
    start: Path | None = None,
    excludes: list[str] | None = None,
    compress_type: str | None = None,
    compress_level: int | None = None,
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
            "'[underline]${{file}}[/underline]' as '${{type}}' ..."
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
        fp = tarfile.open(
            dest,
            f"w:{compress_type}" if compress_type else "w",
            compresslevel=compress_level,
        )
    else:
        fp = tarfile.open(
            dest,
            f"w:{compress_type}" if compress_type else "w",
        )

    _includes = src.rglob("*") if src.is_dir() else [src]
    includes: list[Path] = []

    for path in _includes:
        if excludes and any(path.match(ex) for ex in excludes):
            continue
        includes.append(path)
    del _includes

    with fp:
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
                raise RUValueException(
                    format_str(
                        _(
                            "'[underline]${{path}}[/underline]' is not in the "
                            "subpath of '[underline]${{start}}[/underline]'"
                        ),
                        fmt={"path": str(path), "start": str(start)},
                    ),
                ) from exc
            fp.add(path, arcname, recursive=False)  # Avoid re-adding.
            call_ktrigger(
                IKernelTrigger.on_progress,
                task_name=task_name,
                current=1,
                delta=True,
                more_data={"path": path, "dest": dest},
            )
        call_ktrigger(IKernelTrigger.on_finish_task, task_name=task_name)


def compress_zip(  # pylint: disable=too-many-arguments
    src: Path,
    dest: Path,
    start: Path | None = None,
    excludes: list[str] | None = None,
    compress_level: int | None = None,
    overwrite: bool = False,
) -> None:
    """Compress a zip file to destination.

    Args:
        src (Path): Source file or directory.
        dest (Path): Destination zip file.
        start (Path | None, optional): Start directory. Defaults to None.
        excludes (list[str] | None, optional): List of excluded files.
            Supports glob patterns. Defaults to None.
        compress_level (int | None, optional): Compression level. It can be
            0 to 9. Defaults to None. Only for gzip and bzip2. Ignored for
            others.
        overwrite (bool, optional): Overwrite destination if it exists.
            Defaults to False.
    """

    if not overwrite:
        check_file_exists(dest)
    elif dest.exists():
        rm_recursive(dest)
    task_name = format_str(
        _(
            "Compressing '[underline]${{path}}[/underline]' to "
            "'[underline]${{file}}[/underline]' as '${{type}}' ..."
        ),
        fmt={"path": str(src), "file": str(dest), "type": "zip"},
    )

    if not start:
        start = src.parent

    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as fp:
        _includes = src.rglob("*") if src.is_dir() else [src]
        includes: list[Path] = []
        for path in _includes:
            if excludes and any(path.match(ex) for ex in excludes):
                continue
            includes.append(path)
        del _includes

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
                raise RUValueException(
                    format_str(
                        _(
                            "'[underline]${{path}}[/underline]' is not in the "
                            "subpath of '[underline]${{start}}[/underline]'"
                        ),
                        fmt={"path": str(path), "start": str(start)},
                    ),
                ) from exc
            fp.write(path, arcname, compresslevel=compress_level)
            call_ktrigger(
                IKernelTrigger.on_progress,
                task_name=task_name,
                current=1,
                delta=True,
                more_data={"path": path, "dest": dest},
            )
        call_ktrigger(IKernelTrigger.on_finish_task, task_name=task_name)


def compress_7z(  # pylint: disable=too-many-arguments
    src: Path,
    dest: Path,
    start: Path | None = None,
    excludes: list[str] | None = None,
    overwrite: bool = False,
) -> None:
    """Compress a 7z file to destination.

    Args:
        src (Path): Source file or directory.
        dest (Path): Destination 7z file.
        start (Path | None, optional): Start directory. Defaults to None.
        excludes (list[str] | None, optional): List of excluded files.
            Supports glob patterns. Defaults to None.
        overwrite (bool, optional): Overwrite destination if it exists.
            Defaults to False.
    """

    if not overwrite:
        check_file_exists(dest)
    elif dest.exists():
        rm_recursive(dest)
    task_name = format_str(
        _(
            "Compressing '[underline]${{path}}[/underline]' to "
            "'[underline]${{file}}[/underline]' as '${{type}}' ..."
        ),
        fmt={"path": str(src), "file": str(dest), "type": "7z"},
    )

    if not start:
        start = src.parent

    with py7zr.SevenZipFile(
        dest,
        mode="w",
    ) as fp:
        _includes = src.rglob("*") if src.is_dir() else [src]
        includes: list[Path] = []
        for path in _includes:
            if excludes and any(path.match(ex) for ex in excludes):
                continue
            includes.append(path)
        del _includes

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
                raise RUValueException(
                    format_str(
                        _(
                            "'[underline]${{path}}[/underline]' is not in the "
                            "subpath of '[underline]${{start}}[/underline]'"
                        ),
                        fmt={"path": str(path), "start": str(start)},
                    ),
                ) from exc
            fp.write(path, arcname)
            call_ktrigger(
                IKernelTrigger.on_progress,
                task_name=task_name,
                current=1,
                delta=True,
                more_data={"path": path, "dest": dest},
            )
        call_ktrigger(IKernelTrigger.on_finish_task, task_name=task_name)


def compress_file(  # pylint: disable=too-many-arguments,too-many-branches
    src: Path,
    dest: Path,
    compress_type: str = "gz",
    compress_level: int | None = None,
    overwrite: bool = False,
) -> None:
    """Compress a file to destination.

    Args:
        src (Path): Source file.
        dest (Path): Destination file.
        compress_type (str): Compression type. Default is "gz".
        compress_level (int | None, optional): Compression level. It can be
            0 to 9. Defaults to None. Only for gzip and bzip2. Ignored for
            others.
        overwrite (bool, optional): Overwrite destination if it exists.
            Defaults to False.
    """

    compress_type = compress_type.lower().strip()
    if compress_type == "gzip":
        compress_type = "gz"
    elif compress_type == "bzip2":
        compress_type = "bz2"
    if compress_type not in ["gz", "bz2", "xz"]:
        raise AssertionError

    if not overwrite:
        check_file_exists(dest)
    elif dest.exists():
        rm_recursive(dest)

    if compress_type == "gz":
        fsrc = gzip.open(src, "rb", compresslevel=compress_level)
    elif compress_type == "bz2":
        fsrc = bz2.BZ2File(src, "rb", compresslevel=compress_level)
    elif compress_type == "xz":
        fsrc = lzma.open(src, "rb")
    else:
        raise AssertionError

    with fsrc:
        fsrc.seek(0, os.SEEK_END)
        fsize = fsrc.tell()
        fsrc.seek(0, os.SEEK_SET)
        with open(dest, "wb") as fdst:
            if fsize > COPY_BUFSIZE * 50:
                task_name = format_str(
                    _(
                        "Compressing '[underline]${{path}}[/underline]'"
                        " to '[underline]${{file}}[/underline]'"
                        " as '${{type}}' ..."
                    ),
                    fmt={
                        "path": str(src),
                        "file": str(dest),
                        "type": compress_type,
                    },
                )
                call_ktrigger(
                    IKernelTrigger.on_new_task,
                    task_name=task_name,
                    task_type=IKernelTrigger.TASK_COMPRESS,
                    total=fsize,
                )
                while buf := fsrc.read(COPY_BUFSIZE):
                    call_ktrigger(
                        IKernelTrigger.on_progress,
                        task_name=task_name,
                        current=len(buf),
                        delta=True,
                    )
                    fdst.write(buf)
                call_ktrigger(
                    IKernelTrigger.on_finish_task,
                    task_name=task_name,
                )
            else:
                while buf := fsrc.read(COPY_BUFSIZE):
                    fdst.write(buf)


# We should rewrite this ugly function later.
def compress(  # pylint: disable=too-many-arguments,too-many-branches
    src: Path,
    dest: Path,
    start: Path | None = None,
    excludes: list[str] | None = None,
    compress_type: str | None = None,
    compress_level: int | None = None,
    overwrite: bool = False,
):
    """Compress a file or directory to destination.

    Args:
        src (Path): Source file or directory.
        dest (Path): Destination file.
        start (Path | None, optional): Start directory. Defaults to None.
        excludes (list[str] | None, optional): List of excluded files.
            Supports glob patterns. Defaults to None.
        compress_type (str | None, optional): Compression type. It can be "gz",
            "bz2", "xz", "zip", "7z", "tar.gz", "tar.bz2", "tar.xz" and "tar".
            Defaults to None.
        compress_level (int | None, optional): Compression level. It can be
            0 to 9. Defaults to None. Only for gzip and bzip2. Ignored for
            others.
        overwrite (bool, optional): Overwrite destination if it exists.
            Defaults to False.
    """

    compress_type = compress_type.lower().strip() if compress_type else None
    try:
        if compress_type is None:
            suffix1 = dest.suffix
            suffix2 = dest.suffixes[-2] if len(dest.suffixes) > 1 else None
            if suffix2 == ".tar":
                compress_type = "tar" + suffix1
            elif suffix1:
                compress_type = suffix1[1:]
            else:
                raise RUValueException(
                    format_str(
                        _(
                            "Unable to determine compression type of "
                            "'[underline]${{path}}[/underline]'"
                        ),
                        fmt={"path": str(dest)},
                    ),
                    hint=_("Please specify the compression type explicitly."),
                )
        if compress_type in ["gz", "gzip"]:
            logger.info("Compressing '%s' to '%s' as 'gz' ...", src, dest)
            compress_file(src, dest, "gz", compress_level, overwrite)
        elif compress_type in ["bz2", "bzip2"]:
            logger.info("Compressing '%s' to '%s' as 'bz2' ...", src, dest)
            compress_file(src, dest, "bz2", compress_level, overwrite)
        elif compress_type in ["xz", "lzma"]:
            logger.info("Compressing '%s' to '%s' as 'xz' ...", src, dest)
            compress_file(src, dest, "xz", compress_level, overwrite)
        elif compress_type == "zip":
            logger.info("Compressing '%s' to '%s' as 'zip' ...", src, dest)
            compress_zip(src, dest, start, excludes, compress_level, overwrite)
        elif compress_type == "7z":
            logger.info("Compressing '%s' to '%s' as '7z' ...", src, dest)
            compress_7z(src, dest, start, excludes, overwrite)
        elif compress_type in ["tar.gz", "tgz"]:
            logger.info("Compressing '%s' to '%s' as 'tar.gz' ...", src, dest)
            compress_tarball(
                src,
                dest,
                start,
                excludes,
                "gz",
                compress_level,
                overwrite,
            )
        elif compress_type in ["tar.bz2", "tbz2"]:
            logger.info("Compressing '%s' to '%s' as 'tar.bz2' ...", src, dest)
            compress_tarball(
                src,
                dest,
                start,
                excludes,
                "bz2",
                compress_level,
                overwrite,
            )
        elif compress_type in ["tar.xz", "txz"]:
            logger.info("Compressing '%s' to '%s' as 'tar.xz' ...", src, dest)
            compress_tarball(
                src,
                dest,
                start,
                excludes,
                "xz",
                compress_level,
                overwrite,
            )
        elif compress_type == "tar":
            logger.info("Compressing '%s' to '%s' as 'tar' ...", src, dest)
            compress_tarball(
                src,
                dest,
                start,
                excludes,
                None,
                None,
                overwrite,
            )
        else:
            raise AssertionError
    except AssertionError:
        logger.error(
            "Unsupported compression type: '%s'",
            compress_type,
        )
        raise RUValueException(
            format_str(
                _("Unsupported compression type: '${{type}}'"),
                fmt={"type": compress_type},
            ),
            hint=_(
                "Supported types are 'gz', 'bz2', 'xz', 'zip', '7z', 'tar', "
                "'tar.gz', 'tar.bz2', 'tar.xz'. You can also use the 'tgz', "
                "'txz' and 'tbz2'."
            ),
        ) from None
    except (
        tarfile.TarError,
        zipfile.BadZipfile,
        zipfile.LargeZipFile,
        lzma.LZMAError,
        py7zr.exceptions.ArchiveError,
        OSError,
    ) as exc:
        logger.exception(
            "Failed to compress '%s' to '%s'.",
            src,
            dest,
        )
        raise RUValueException(
            format_str(
                _("Failed to compress '${{src}}' to '${{dest}}': '${{exc}}'"),
                fmt={"src": src, "dest": dest, "exc": str(exc)},
            )
        ) from exc
