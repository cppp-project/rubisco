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
File utilities.
"""

import os
import tempfile
import shutil
from pathlib import Path

from repoutils.log import logger

__all__ = [
    "system_tempdir",
    "rm_recursive",
    "new_tempdir",
    "new_tempfile",
    "register_tempdir",
    "unregister_tempdir",
    "remove_temp",
    "cleanup_tempdirs",
]


def system_tempdir():
    """Get the system temporary directory.

    Returns:
        Path: The system temporary directory.
    """

    return Path(tempfile.gettempdir()).absolute()


def rm_recursive(path: Path, strict=True):
    """Remove a file or directory recursively.

    Args:
        path (Path): The path to remove.
        strict (bool): Raise an exception if error occurs.

    Raises:
        OSError: If strict is True and an error occurs.
    """

    path = path.absolute()
    if not path.exists():
        return
    try:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            os.remove(path)
        logger.info("Removed '%s'.", str(path))
    except OSError:
        if strict:
            raise
        logger.warning("Failed to remove '%s'.", str(path))


tempdirs: list[Path] = []


def new_tempdir(prefix: str = "", suffix: str = ""):
    """Create temporary directory.

    Args:
        suffix (str): The suffix of the temporary directory.

    Returns:
        str: The temporary directory.
    """

    path = Path(
        tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=tempfile.gettempdir())
    ).absolute()

    tempdirs.append(path)
    logger.info("Created temporary directory '%s'.", str(path))

    return path


def new_tempfile(prefix: str = "", suffix: str = ""):
    """Create temporary file.

    Args:
        suffix (str): The suffix of the temporary file.

    Returns:
        str: The temporary file.
    """

    path = Path(
        tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=tempfile.gettempdir())[1]
    ).absolute()

    tempdirs.append(path)
    logger.info("Created temporary file '%s'.", str(path))

    return path


def register_tempdir(path: Path):
    """Register temporary directory.

    Args:
        path (Path): The path to register.
    """

    tempdirs.append(path)


def unregister_tempdir(path: Path):
    """Unregister temporary directory.

    Args:
        path (Path): The path to unregister.
    """

    try:
        tempdirs.remove(path)
    except ValueError:
        pass


def remove_temp(path: Path, strict=True):
    """Remove temporary file or directory.

    Args:
        path (Path): The path to remove.
        strict (bool): Raise an exception if error occurs.
    """

    try:
        rm_recursive(path, strict=False)
        logger.info("Removed '%s'.", str(path))
    except OSError:
        if strict:
            raise
        logger.warning("Failed to remove '%s'.", str(path))
    finally:
        unregister_tempdir(path)


def cleanup_tempdirs():
    """Cleanup temporary directories."""
    for path in tempdirs:
        rm_recursive(path, strict=False)
    tempdirs.clear()


if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    print("Creating temporary directory...")
    tempdir = new_tempdir("cppp-repoutils-test-tempdir")
    print(f"Temporary directory: {tempdir}")

    print("Creating temporary file1...")
    tempfile1 = new_tempfile("cppp-repoutils-test-file1")
    print(f"Temporary file: {tempfile1}")

    print("Creating temporary file2...")
    tempfile2 = new_tempfile("cppp-repoutils-test-file2")
    print(f"Temporary file2: {tempfile2}")

    print("Removing temporary file1...")
    remove_temp(tempfile1)

    print("Cleaning up temporary directories...")
    cleanup_tempdirs()

    print("Done.")
