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
Compression utils.
"""

from pathlib import Path
import tarfile
import zipfile
from cppp_repoutils.utils.log import logger
from cppp_repoutils.utils.output import ProgressBar
from cppp_repoutils.utils.ignore_file import IgnoreChecker
from cppp_repoutils.utils.nls import _
from cppp_repoutils.utils.yesno import yesno


def compress_tar(
    name: Path,
    directory: Path,
    arcname: Path,
    ign_checker: IgnoreChecker,
    compress_type: str,
):
    """Compress directory to tar file.

    Args:
        name (Path): The archive file name (with path).
        directory (Path): Directory to compress.
        arcname (Path): The alternative name for the file in the archive.
        ign_checker (IgnoreChecker): Ignore file checker.
        compress_type (str): Compression type. Can be 'gz', 'bz2', 'xz' or ''(no compression).

    Raises:
        FileExistsError: If the file already exists and user doesn't want to overwrite it.
    """

    if name.exists():
        logger.warning("'%s' already exists.", name)
        if not yesno(
            _("{yellow}{underline}{path}{reset} already exists. Overwrite?"),
            default=0,
            fmt={"path": name},
        ):
            raise FileExistsError(name)

    with tarfile.open(name, ":".join(["w", compress_type])) as archive:
        total_length = sum(1 for _ in directory.rglob("*"))
        for file in ProgressBar(
            directory.rglob("*"),
            desc=_(
                "Compressing '{underline}{name}{reset}' into '{underline}{archive}{reset}' ..."
            ),
            total=total_length,
            desc_fmt={"name": directory, "archive": name},
        ):
            file: Path
            if file.is_dir() or ign_checker(file):
                continue
            archive.add(
                file, arcname / file.relative_to(directory.parent), recursive=False
            )
    logger.info("Compressed '%s' into '%s'.", directory, name)


def compress_zip(
    name: Path, directory: Path, arcname: Path, ign_checker: IgnoreChecker
):
    """Compress directory to zip file.

    Args:
        name (Path): The archive file name (with path).
        directory (Path): Directory to compress.
        arcname (Path): The alternative name for the file in the archive.
        ign_checker (IgnoreChecker): Ignore file checker.

    Raises:
        FileExistsError: If the file already exists and user doesn't want to overwrite it.
    """

    if name.exists():
        logger.warning("'%s' already exists.", name)
        if not yesno(
            _("{yellow}{underline}{path}{reset} already exists. Overwrite?"),
            default=0,
            fmt={"path": name},
        ):
            raise FileExistsError(name)

    with zipfile.ZipFile(name, "w", compresslevel=9) as archive:
        total_length = sum(1 for _ in directory.rglob("*"))
        for file in ProgressBar(
            directory.rglob("*"),
            desc=_(
                "Compressing '{underline}{name}{reset}' into '{underline}{archive}{reset}' ..."
            ),
            total=total_length,
            desc_fmt={"name": directory, "archive": name},
        ):
            file: Path
            if file.is_dir() or ign_checker(file):
                continue
            archive.write(
                file,
                arcname / file.relative_to(directory.parent),
                compress_type=zipfile.ZIP_DEFLATED,
            )
    logger.info("Compressed '%s' into '%s'.", directory, name)


def compress(
    name: Path,
    directory: Path,
    arcname: Path,
    ign_checker: IgnoreChecker,
    compress_type: str,
):
    """Compress directory to a archive file.

    Args:
        name (Path): The archive file name (with path).
        directory (Path): Directory to compress.
        arcname (Path): The alternative name for the file in the archive.
        ign_checker (IgnoreChecker): Ignore file checker.
        compress_type (str): Compression type.
            Can be 'tar', 'tar.gz', 'tar.bz2', 'tar.xz', 'zip' or ''(no compression).

    Raises:
        ValueError: If the compress_type is unknown.
        FileExistsError: If the file already exists and user doesn't want to overwrite it.
    """

    match (compress_type):
        case "tar":
            compress_tar(name, directory, arcname, ign_checker, "")
        case "tar.gz":
            compress_tar(name, directory, arcname, ign_checker, "gz")
        case "tar.bz2":
            compress_tar(name, directory, arcname, ign_checker, "bz2")
        case "tar.xz":
            compress_tar(name, directory, arcname, ign_checker, "xz")
        case "zip":
            compress_zip(name, directory, arcname, ign_checker)
        case _:
            raise ValueError(
                _("Unknown compress_type: {type}").format(type=compress_type)
            )


def extract_tar(archive_path: Path, target_directory: Path, compress_type: str):
    """Extract tar file.

    Args:
        archive_path (Path): The archive file path.
        target_directory (Path): The destination directory.
        compress_type (str): Compression type. Can be 'gz', 'bz2', 'xz' or ''(tar).

    Raises:
        FileExistsError: If the file already exists and user doesn't want to overwrite it.
    """

    with tarfile.open(archive_path, ":".join(["r", compress_type])) as archive:
        total_length = sum(1 for _ in archive.getmembers())
        for member in ProgressBar(
            archive.getmembers(),
            desc=_(
                "Extracting '{underline}{archive}{reset}' into '{underline}{directory}{reset}' ..."
            ),
            total=total_length,
            desc_fmt={"archive": archive_path, "directory": target_directory},
        ):
            member: tarfile.TarInfo
            if member.isdir():
                continue
            output_path = target_directory / member.name
            if output_path.exists():
                logger.warning("'%s' already exists.", output_path)
                if not yesno(
                    _("{yellow}{underline}{path}{reset} already exists. Overwrite?"),
                    default=0,
                    fmt={"path": output_path},
                ):
                    raise FileExistsError(output_path)
            archive.extract(member, target_directory)
    logger.info("Extracted '%s' into '%s'.", archive_path, target_directory)


def extract_zip(archive_path: Path, target_directory: Path):
    """Extract zip file.

    Args:
        archive_path (Path): The archive file path.
        target_directory (Path): The destination directory.

    Raises:
        FileExistsError: If the file already exists and user doesn't want to overwrite it.
    """

    with zipfile.ZipFile(archive_path, "r") as archive:
        total_length = sum(1 for _ in archive.infolist())
        for member in ProgressBar(
            archive.infolist(),
            desc=_(
                "Extracting '{underline}{archive}{reset}' into '{underline}{directory}{reset}' ..."
            ),
            total=total_length,
            desc_fmt={"archive": archive_path, "directory": target_directory},
        ):
            member: zipfile.ZipInfo
            if member.is_dir():
                continue
            output_path = target_directory / member.filename
            if output_path.exists():
                logger.warning("'%s' already exists.", output_path)
                if not yesno(
                    _("{yellow}{underline}{path}{reset} already exists. Overwrite?"),
                    default=0,
                    fmt={"path": output_path},
                ):
                    raise FileExistsError(output_path)
            archive.extract(member, target_directory)
    logger.info("Extracted '%s' into '%s'.", archive_path, target_directory)


def extract(archive_path: Path, target_directory: Path, compress_type: str):
    """Extract archive file.

    Args:
        archive_path (Path): The archive file path.
        target_directory (Path): The destination directory.
        compress_type (str): Compression type.
            Can be 'tar', 'tar.gz', 'tar.bz2', 'tar.xz', 'zip' or ''(no compression).

    Raises:
        ValueError: If the compress_type is unknown.
    """

    match (compress_type):
        case "tar":
            extract_tar(archive_path, target_directory, "")
        case "tar.gz":
            extract_tar(archive_path, target_directory, "gz")
        case "tar.bz2":
            extract_tar(archive_path, target_directory, "bz2")
        case "tar.xz":
            extract_tar(archive_path, target_directory, "xz")
        case "zip":
            extract_zip(archive_path, target_directory)
        case _:
            raise ValueError(
                _("Unknown compress_type: {type}").format(type=compress_type)
            )


if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    output = Path(input("Archive output path: "))
    compress_dir = Path(input("Directory to compress: "))
    archive_type = input("Archive type: ")
    compress(output, compress_dir, Path("."), lambda x: False, archive_type)

    input_file = Path(input("Archive input path: "))
    extract_dir = Path(input("Directory to extract: "))
    archive_type = input("Archive type: ")
    extract(input_file, extract_dir, archive_type)

    print("Done.")
