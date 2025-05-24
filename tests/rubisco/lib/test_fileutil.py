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

"""Test rubisco.lib.fileutil module."""

import shutil
from pathlib import Path

import pytest

from rubisco.lib.exceptions import RUShellExecutionError
from rubisco.lib.fileutil import (
    TemporaryObject,
    find_command,
    human_readable_size,
)


class TestFileUtil:
    """Test file util."""

    def test_new_tempfile(self) -> None:
        """Test new_tempfile."""
        temp = TemporaryObject.new_file()
        if not temp.is_file():
            raise AssertionError
        if not temp.temp_type == TemporaryObject.TYPE_FILE:
            raise AssertionError
        temp.remove()
        if temp.path.exists():
            raise AssertionError

    def test_new_tempdir(self) -> None:
        """Test new_tempdir."""
        temp = TemporaryObject.new_directory()
        if not temp.is_dir():
            raise AssertionError
        if not temp.temp_type == TemporaryObject.TYPE_DIRECTORY:
            raise AssertionError
        temp.remove()
        if temp.path.exists():
            raise AssertionError

    def test_temp_object_context_manager(self) -> None:
        """Test temp object context manager."""
        temp_file_path = "/"
        with TemporaryObject.new_file() as temp:
            temp_file_path = temp.path
            if not temp.is_file():
                raise AssertionError
            if not temp.temp_type == TemporaryObject.TYPE_FILE:
                raise AssertionError
        if temp_file_path.exists():
            raise AssertionError

        with TemporaryObject.new_directory() as temp:
            temp_file_path = temp.path
            if not temp.is_dir():
                raise AssertionError
            if not temp.temp_type == TemporaryObject.TYPE_DIRECTORY:
                raise AssertionError
        if temp_file_path.exists():
            raise AssertionError

    def test_temp_object_cleanup(self) -> None:
        """Test temp object cleanup."""
        temp1 = TemporaryObject.new_file()
        temp2 = TemporaryObject.new_directory()
        temp3 = TemporaryObject.new_file("PREFIX-", "-SUFFIX")
        temp4 = TemporaryObject.new_directory("PREFIX-", "-SUFFIX")
        if (
            not temp1.is_file()
            or not temp2.is_dir()
            or not temp3.is_file()
            or not temp4.is_dir()
        ):
            raise AssertionError
        TemporaryObject.cleanup()
        if (
            temp1.path.exists()
            or temp2.path.exists()
            or temp3.path.exists()
            or temp4.path.exists()
        ):
            raise AssertionError

    def test_temp_object_register_tempobject(self) -> None:
        """Test temp object register_tempobject."""
        Path("test_tempfile").touch()
        Path("test_tempdir").mkdir(parents=True, exist_ok=True)
        temp1 = TemporaryObject.register_tempobject(Path("test_tempfile"))
        temp2 = TemporaryObject.register_tempobject(Path("test_tempdir"))
        TemporaryObject.cleanup()
        if (
            temp1.is_file()
            or temp2.is_dir()
            or temp1.path.exists()
            or temp2.path.exists()
        ):
            raise AssertionError

    def test_temp_object_move(self) -> None:
        """Test temp object's ownership transfer."""
        temp = TemporaryObject.new_file()
        temp_path = temp.move()
        if temp_path != temp.path:
            raise AssertionError
        TemporaryObject.cleanup()
        if not temp_path.exists():
            raise AssertionError

    def test_temp_object_remove(self) -> None:
        """Test temp object's removal."""
        temp = TemporaryObject.new_file()
        temp.remove()
        if temp.path.exists():
            raise AssertionError
        TemporaryObject.cleanup()

    def test_human_readable_size(self) -> None:
        """Test human_readable_size."""
        if (
            human_readable_size(1023) != "1023.00B"  # pylint: disable=R0916
            or human_readable_size(1024) != "1.00KiB"
            or human_readable_size(1024**2) != "1.00MiB"
            or human_readable_size(1024**3) != "1.00GiB"
            or human_readable_size(1024**4) != "1.00TiB"
            or human_readable_size(1024**5) != "1.00PiB"
            or human_readable_size(1024**6) != "1.00EiB"
            or human_readable_size(0) != "0.00B"
        ):
            raise AssertionError

    def test_find_command(self) -> None:
        """Test find_command."""
        if find_command("whoami") != shutil.which("whoami"):
            raise AssertionError

        pytest.raises(
            RUShellExecutionError,
            find_command,
            "_Not_Exist_Command_",
            strict=True,
        )

        if find_command("_Not_Exist_Command_", strict=False) is not None:
            raise AssertionError
