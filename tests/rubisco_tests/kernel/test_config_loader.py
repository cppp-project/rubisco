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

"""Test for rubisco config loader."""

from pathlib import Path

import pytest

from rubisco.kernel.config_loader import RUConfiguration


def test_load() -> None:
    """Test for rubisco config loader."""
    res: dict[str, object] = {
        "a": 2,
        "b": ["B", 1, 2, 3],
        "c": [1, 2, 3, 4],
        "d": {
            "aa": 11,
            "bb": "bb",
            "cc": [11, 22],
            "dd": {"a": 1, "xxxx": [{"a": 1}, {"b": 2}], "b": 1},
            "ee": "ef",
        },
        "includes": ["test.include.json"],
    }
    config = RUConfiguration.load_from_file(Path("tests/test.json5"))
    d = dict(config)
    if d != res:
        pytest.fail(f"Expect {res}, got {d}")
