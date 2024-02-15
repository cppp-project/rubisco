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


def compress_tar_xz(
    name: Path, directory: Path, arcname: Path, ign_checker: IgnoreChecker
):
    """Compress directory to tar.xz.

    Args:
        name (Path): Directory to compress.
        directory (Path): Directory to compress.
        arcname (Path): The alternative name for the file in the archive.
        ign_checker (IgnoreChecker): Ignore file checker.
    """

    if name.exists():
        logger.warning("'%s' already exists.", name)
        if not yesno(
            _("{yellow}{underline}{path}{reset} already exists. Overwrite?"),
            default=0,
            fmt={"path": name},
        ):
            raise FileExistsError(name)

    with tarfile.open(name, "w:xz") as archive:
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
    """Compress directory to zip.

    Args:
        name (Path): Directory to compress.
        directory (Path): Directory to compress.
        arcname (Path): The alternative name for the file in the archive.
        ign_checker (IgnoreChecker): Ignore file checker.
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


if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    output = Path(input("tar.xz output path: "))
    compress_dir = Path(input("Directory to compress: "))
    compress_tar_xz(output, compress_dir, Path(), lambda x: False)

    output = Path(input("zip output path: "))
    compress_dir = Path(input("Directory to compress: "))
    compress_zip(output, compress_dir, Path(), lambda x: False)
