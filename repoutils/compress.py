# -*- coding: utf-8 -*-
# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2024 The C++ Plus Project.
# This file is part of the cppp-repoutils.
#
# cppp-repoutils is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# cppp-repoutils is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Compress utils.
This module is used to decompress or compress files and directories for cppp-compress and 
cppp-repoutils, support Tar, GZip, 7-Zip and Zip.
"""

from abc import ABC, abstractmethod
import os
import tarfile
import gzip
from pathlib import Path
from typing import Any
import zipfile

from repoutils.constants import APP_NAME
from repoutils.constants import DEFAULT_CHARSET
from repoutils.fileutil import (
    system_tempdir,
    rm_recursive,
    remove_temp,
    unregister_tempdir,
)
from repoutils.nls import _
from repoutils.log import logger
from repoutils.output import ProgressBar
from repoutils.yesno import yesno


class ArchiveError(Exception):
    """Archive error."""

    def __init__(self, message: str, *args):
        super().__init__(message, *args)


# The copy buffer size.
COPY_BUFSIZE = 1024 * 1024 if (os.name == "nt") else 64 * 1024


class ArchiveCallback(ABC):
    """Archive event callback."""

    archive_event: str
    archive_path: Path
    archive_type: str
    total_size: int

    @abstractmethod
    def on_start(self) -> None:
        """On archive start event."""

    @abstractmethod
    def on_progress(self, delta: int) -> None:
        """On progress update event.

        Args:
            delta (int): The delta size.
        """

    @abstractmethod
    def on_file(self, file_abspath: Path, file_relpath: Path) -> None:
        """On a file extracted or compressed event.

        Args:
            file_abspath (Path): The file absolute path.
            file_relpath (Path): The file relative path.
        """

    @abstractmethod
    def on_exception(
        self, file_abspath: Path, file_relpath: Path, exception: Exception
    ) -> None:
        """On a file compress or extract error event.
            If you want to abort, you can raise the exception in this event.

        Args:
            file_abspath (Path): The file absolute path.
            file_relpath (Path): The file relative path.
            exception (Exception): The exception.
        """

    @abstractmethod
    def on_finished(self) -> None:
        """On archive finished event."""

    @abstractmethod
    def on_password(self, file_relpath: Path, fileinfo: Any) -> bytes:
        """On password required event.

        Args:
            file_relpath (Path): The file relative path.
            fileinfo (Any): The file info.

        Returns:
            bytes: The password.
        """


def gzip_moreinfo(archive_path: Path) -> tuple[str, int]:
    """Get GZip file more info.

    Args:
        archive_path (Path): The GZip archive path.

    Returns:
        tuple[str, int]: The FNAME and ISIZE.
    """

    archive_path = archive_path.resolve()
    with gzip.open(archive_path, "rb"):
        pass  # Check gzip file is valid.
    with open(archive_path, "rb") as archive_file:
        # Get the ISIZE in the archive.
        archive_file.seek(-4, os.SEEK_END)
        isize = int.from_bytes(archive_file.read(4), "little")
        # Get the FNAME in the archive.
        archive_file.seek(0x0A, os.SEEK_SET)
        # Read the FNAME until the null byte.
        fname = b""
        while True:
            byte = archive_file.read(1)
            if byte == b"\x00":
                break
            fname += byte
        return fname.decode("Latin-1"), isize


def extract_gzip(
    archive_path: Path, output_path: Path, callback: ArchiveCallback
) -> Path:
    """Extract Gzip file.

    Args:
        archive_path (Path): The Gzip archive path.
        output_path (Path): Output directory.
        callback (ArchiveCallback): The callback.

    Returns:
        Path: The extracted file name.
    """

    archive_path = archive_path.resolve()
    output_path = output_path.absolute()

    with gzip.open(archive_path, "rb") as archive_file:
        # Prepare for extract.
        fname, isize = gzip_moreinfo(archive_path)
        output_file_path = output_path / fname
        callback.archive_event = "extract"
        callback.archive_path = archive_path
        callback.archive_type = "gzip"
        callback.total_size = isize

        # Start extract.
        callback.on_start()
        if output_file_path.exists():
            exc = FileExistsError(filename=output_file_path)
            callback.on_exception(output_file_path, fname, exc)
        try:
            os.makedirs(output_file_path.parent, exist_ok=True)
            with open(output_file_path, "wb") as output_file:
                while True:
                    buf = archive_file.read(COPY_BUFSIZE)
                    if not buf:
                        break
                    delta = output_file.write(buf)
                    output_file.flush()
                    callback.on_progress(delta)
            callback.on_file(output_file_path, fname)

        except OSError as exc:
            callback.on_exception(output_file_path, fname, exc)

    # Finished.
    callback.on_finished()
    return output_file_path


def extract_tar(
    archive_path: Path,
    output_path: Path,
    callback: ArchiveCallback,
    create_dir_if_not_single: bool = True,
) -> Path:
    """Extract Tar file.

    Args:
        archive_path (Path): The Tar archive path.
        output_path (Path): Output directory.
        callback (ArchiveCallback): The callback.
        create_dir_if_not_single (bool, optional): Create directory if not single
                (in the archive root). Defaults to True.

    Returns:
        Path: The extracted file name, if the archive has only one file or directory
                (in the archive root).
    """

    archive_path = archive_path.resolve()
    output_path = output_path.absolute()

    with tarfile.open(archive_path, "r") as archive_file:
        # Prepare for extract.
        total_size = sum(member.size for member in archive_file.getmembers())
        callback.archive_event = "extract"
        callback.archive_path = archive_path
        callback.archive_type = "tar"
        callback.total_size = total_size

        # Start extract.
        callback.on_start()
        # The root directory list of the archive.
        root_list = [
            member for member in archive_file.getmembers() if "/" not in member.name
        ]
        is_single = len(root_list) == 1
        if not is_single and create_dir_if_not_single:
            # Create directory if not single.
            os.makedirs(output_path, exist_ok=True)
            output_path = output_path / archive_path.stem
        for member in archive_file.getmembers():
            output_file_path = output_path / member.name
            try:
                archive_file.extract(member, output_path)
                callback.on_progress(member.size)
                callback.on_file(output_file_path, member.name)
            except OSError as exc:
                callback.on_exception(output_file_path, member.name, exc)

        # Finished.
        callback.on_finished()
        return Path(archive_file.getnames()[0] if is_single else output_path)


def extract_zip(
    archive_path: Path,
    output_path: Path,
    callback: ArchiveCallback,
    create_dir_if_not_single: bool = True,
) -> Path:
    """Extract Zip file.

    Args:
        archive_path (Path): The Zip archive path.
        output_path (Path): Output directory.
        callback (ArchiveCallback): The callback.
        create_dir_if_not_single (bool, optional): Create directory if not single
                (in the archive root). Defaults to True.

    Returns:
        Path: The extracted file name, if the archive has only one file or directory
                (in the archive root).
    """

    archive_path = archive_path.resolve()
    output_path = output_path.absolute()

    with zipfile.ZipFile(archive_path, "r") as archive_file:
        # Prepare for extract.
        total_size = sum(member.file_size for member in archive_file.infolist())
        callback.archive_event = "extract"
        callback.archive_path = archive_path
        callback.archive_type = "zip"
        callback.total_size = total_size

        # Start extract.
        callback.on_start()
        # The root directory list of the archive.
        root_list = [
            member for member in archive_file.infolist() if "/" not in member.filename
        ]
        is_single = len(root_list) == 1
        if not is_single and create_dir_if_not_single:
            # Create directory if not single.
            os.makedirs(output_path, exist_ok=True)
            output_path = output_path / archive_path.stem
        for member in archive_file.infolist():
            output_file_path = output_path / member.filename
            try:
                try:
                    archive_file.extract(member, output_path)
                except RuntimeError:
                    if member.flag_bits & 0x01:  # May be encrypted.
                        password = callback.on_password(member.filename, member)
                        archive_file.extract(member, output_path, pwd=password)
                        archive_file.setpassword(password)
                    else:  # Maybe other error.
                        raise
                callback.on_progress(member.file_size)
                callback.on_file(output_file_path, member.filename)

            except (OSError, RuntimeError) as exc:
                callback.on_exception(output_file_path, member.filename, exc)

        # Finished.
        callback.on_finished()
        return Path(archive_file.infolist()[0].filename if is_single else output_path)


def extract(
    archive_path: Path,
    archive_type: str,
    output_path: Path,
    recursive: bool,
) -> Path:
    class _MyCallback(ArchiveCallback):
        progress_bar: ProgressBar

        def on_start(self) -> None:
            logger.info(
                "Extracting archive '%s' to '%s' ...", self.archive_path, output_path
            )
            self.progress_bar = ProgressBar(
                _("Extracting '{file}' to '{path}' ..."),
                self.total_size,
                desc_fmt={
                    "file": self.archive_path.name,
                    "path": output_path,
                },
            )

        def on_progress(self, delta: int) -> None:
            self.progress_bar.add(delta)

        def on_file(self, file_abspath: Path, file_relpath: Path) -> None:
            logger.debug("Extracted '%s' to '%s'.", file_relpath, file_abspath)

        def on_exception(
            self, file_abspath: Path, file_relpath: Path, exception: Exception
        ) -> None:
            if isinstance(exception, FileExistsError):  # File exists.
                need_remove = yesno(
                    _("'{file}' exists, remove it?"),
                    default=0,
                    fmt={"file": file_abspath},
                    color="yellow",
                )
                if need_remove:
                    rm_recursive(file_abspath)
                else:
                    logger.exception(
                        "Failed to extract '%s' to '%s'.",
                        file_relpath,
                        file_abspath,
                        exc_info=exception,
                    )
                    raise exception
            else:
                logger.exception(
                    "Failed to extract '%s' to '%s'.",
                    file_relpath,
                    file_abspath,
                    exc_info=exception,
                )
                raise exception

        def on_finished(self) -> None:
            logger.info("Archive extracted.")
            self.progress_bar.finish()

        def on_password(self, file_relpath: Path, fileinfo: Any) -> bytes:
            pass


if __name__ == "__main__":

    class _TestCallback(ArchiveCallback):
        progress_bar: ProgressBar

        def on_start(self) -> None:
            self.progress_bar = ProgressBar(
                _("Extracting '{file}' to '{path}' ..."),
                self.total_size,
                desc_fmt={
                    "file": self.archive_path.name,
                    "path": "/tmp",
                },
            )

        def on_progress(self, delta: int) -> None:
            self.progress_bar.add(delta)

        def on_file(self, file_abspath: Path, file_relpath: Path) -> None:
            pass

        def on_exception(
            self, file_abspath: Path, file_relpath: Path, exception: Exception
        ) -> None:
            print("x")
            raise exception

        def on_finished(self) -> None:
            self.progress_bar.finish()

        def on_password(self, file_relpath: Path, fileinfo: Any) -> bytes:
            pass

    c = _TestCallback()
    gz = extract_gzip(Path("/home/user/test.tar.gz"), Path("/tmp"), c)
    print(gz)
    extract_tar(gz, Path("/tmp"), c, True)
