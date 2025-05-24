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

"""Test rubisco.lib.convert module."""

import math

import pytest

from rubisco.lib.convert import convert_to


class TestConvertTo:
    """Test convert_to."""

    def test_convert_to_bool(self) -> None:
        """Test convert_to bool."""
        if (
            convert_to("true", as_type=bool) is not True
            or convert_to("False", as_type=bool) is not False
            or convert_to("Yes", as_type=bool) is not True
            or convert_to("NO", as_type=bool) is not False
        ):
            pytest.fail("convert_to bool failed")
        if (
            convert_to("oN", as_type=bool) is not True
            or convert_to("Off", as_type=bool) is not False
            or convert_to("1", as_type=bool) is not True
            or convert_to("0", as_type=bool) is not False
        ):
            pytest.fail("convert_to bool failed")

    def test_convert_to_int(self) -> None:
        """Test convert_to int."""
        if (
            convert_to("1", as_type=int) != 1
            or convert_to("10", as_type=int) != 10  # noqa: PLR2004
            or convert_to("100", as_type=int) != 100  # noqa: PLR2004
            or convert_to("1000", as_type=int) != 1000  # noqa: PLR2004
            or convert_to("32767", as_type=int) != 32767  # noqa: PLR2004
        ):
            pytest.fail("convert_to int failed for positive integers.")

        if (
            convert_to("-1", as_type=int) != -1
            or convert_to("-10", as_type=int) != -10  # noqa: PLR2004
            or convert_to("-100", as_type=int) != -100  # noqa: PLR2004
            or convert_to("-1000", as_type=int) != -1000  # noqa: PLR2004
            or convert_to("-32767", as_type=int) != -32767  # noqa: PLR2004
        ):
            pytest.fail("convert_to int failed for negative integers.")

        if (
            convert_to("0", as_type=int) != 0
            or convert_to("00", as_type=int) != 0
            or convert_to("000", as_type=int) != 0
            or convert_to("0000", as_type=int) != 0
            or convert_to("00000", as_type=int) != 0
        ):
            pytest.fail("convert_to int failed for zero.")

        if (
            convert_to("0x1", as_type=int) != 1
            or convert_to("0x10", as_type=int) != 16  # noqa: PLR2004
            or convert_to("0x100", as_type=int) != 256  # noqa: PLR2004
            or convert_to("0x1000", as_type=int) != 4096  # noqa: PLR2004
            or convert_to("0x7FFF", as_type=int) != 32767  # noqa: PLR2004
        ):
            pytest.fail("convert_to int failed for hexadecimal integers.")

        if (
            convert_to("0o1", as_type=int) != 1
            or convert_to("0o10", as_type=int) != 8  # noqa: PLR2004
            or convert_to("0o100", as_type=int) != 64  # noqa: PLR2004
            or convert_to("0o1000", as_type=int) != 512  # noqa: PLR2004
            or convert_to("0o777", as_type=int) != 511  # noqa: PLR2004
        ):
            pytest.fail("convert_to int failed for octal integers.")

        if (
            convert_to("0b1", as_type=int) != 1
            or convert_to("0b10", as_type=int) != 2  # noqa: PLR2004
            or convert_to("0b100", as_type=int) != 4  # noqa: PLR2004
            or convert_to("0b1000", as_type=int) != 8  # noqa: PLR2004
            or convert_to("0b11111111", as_type=int) != 255  # noqa: PLR2004
        ):
            pytest.fail("convert_to int failed for binary integers.")

        if (
            convert_to("1K", as_type=int) != 1024  # noqa: PLR2004
            or convert_to("1kb", as_type=int) != 1024  # noqa: PLR2004
            or convert_to("1kib", as_type=int) != 1024  # noqa: PLR2004
            or convert_to("1m", as_type=int) != 1024 * 1024
        ):
            pytest.fail("convert_to int failed for size.")

        if (
            convert_to("1Mb", as_type=int) != 1024 * 1024
            or convert_to("1mib", as_type=int) != 1024 * 1024
            or convert_to("1g", as_type=int) != 1024 * 1024 * 1024
            or convert_to("1GiB", as_type=int) != 1024 * 1024 * 1024
            or convert_to("4321890b", as_type=int) != 4321890  # noqa: PLR2004
        ):
            pytest.fail("convert_to int failed for size.")

    def test_convert_to_float(self) -> None:
        """Test convert_to float."""
        if (
            convert_to("1.0", as_type=float) != 1.0
            or convert_to("1.00", as_type=float) != 1.0
            or convert_to("1.000", as_type=float) != 1.0
            or convert_to("1.0000", as_type=float) != 1.0
            or convert_to("3.141592653589793", as_type=float) != math.pi
        ):
            pytest.fail("convert_to float failed for positive floats.")

        if (
            convert_to("-1.0", as_type=float) != -1.0
            or convert_to("-1.00", as_type=float) != -1.0
            or convert_to("-1.000", as_type=float) != -1.0
            or convert_to("-1.0000", as_type=float) != -1.0
            or convert_to("-3.141592653589793", as_type=float) != -math.pi
        ):
            pytest.fail("convert_to float failed for negative floats.")

        if (
            convert_to("0.0", as_type=float) != 0.0
            or convert_to("0.00", as_type=float) != 0.0
            or convert_to("0.000", as_type=float) != 0.0
            or convert_to("0.0000", as_type=float) != 0.0
            or convert_to("0.00000", as_type=float) != 0.0
        ):
            pytest.fail("convert_to float failed for zero.")

        if (
            convert_to("1e1", as_type=float) != 10.0  # noqa: PLR2004
            or convert_to("1e2", as_type=float) != 100.0  # noqa: PLR2004
            or convert_to("1e3", as_type=float) != 1000.0  # noqa: PLR2004
            or convert_to("1.113E6", as_type=float) != 1113000.0  # noqa: PLR2004
        ):
            pytest.fail("convert_to float failed for scientific notation.")

        if (
            convert_to("1.113e6", as_type=float) != 1113000.0  # noqa: PLR2004
            or convert_to("1.113e-6", as_type=float) != 0.000001113  # noqa: PLR2004
            or convert_to("1.113e+6", as_type=float) != 1113000.0  # noqa: PLR2004
            or convert_to("1.113e-06", as_type=float) != 0.000001113  # noqa: PLR2004
            or convert_to("1.113e+06", as_type=float) != 1113000.0  # noqa: PLR2004
        ):
            pytest.fail("convert_to float failed for scientific notation.")

        if (
            convert_to("PI", as_type=float) != math.pi
            or convert_to("e", as_type=float) != math.e
        ):
            pytest.fail("convert_to float failed for PI and e.")

    def test_convert_to_str(self) -> None:
        """Test convert_to str."""
        if (
            convert_to("hello", as_type=str) != "hello"
            or convert_to("hello world", as_type=str) != "hello world"
            or convert_to("hello world!", as_type=str) != "hello world!"
        ):
            pytest.fail("convert_to str failed for strings.")

    def test_convert_to_sequence(self) -> None:
        """Test convert_to list, tuple, set."""
        if (
            convert_to("1,2,3", as_type=list) != ["1", "2", "3"]
            or convert_to("1,2,3,4", as_type=list) != ["1", "2", "3", "4"]
            or convert_to("1,2,3,4,5", as_type=list)
            != [
                "1",
                "2",
                "3",
                "4",
                "5",
            ]
            or convert_to("?,X,Y,Z", as_type=list) != ["?", "X", "Y", "Z"]
        ):
            pytest.fail("convert_to list failed for lists.")

        if (
            convert_to("1,2,3", as_type=tuple) != ("1", "2", "3")
            or convert_to("1,2,3,4", as_type=tuple) != ("1", "2", "3", "4")
            or convert_to("?,X,Y,Z", as_type=tuple) != ("?", "X", "Y", "Z")
        ):
            pytest.fail("convert_to tuple failed for tuples.")

        if (
            convert_to("1,2,3", as_type=set) != {"1", "2", "3"}
            or convert_to("1,2,3,4", as_type=set) != {"1", "2", "3", "4"}
            or convert_to("1,2,3,4,5", as_type=set) != {"1", "2", "3", "4", "5"}
            or convert_to("?,X,Y,Z", as_type=set) != {"?", "X", "Y", "Z"}
            or convert_to("1,1,2,2,3,3", as_type=set) != {"1", "2", "3"}
        ):
            pytest.fail("convert_to set failed for sets.")

    def test_convert_to_dict(self) -> None:
        """Test convert_to dict."""
        if convert_to('{"a": 1, "b": 2}', as_type=dict) != {
            "a": 1,
            "b": 2,
        } or convert_to('{"1": 3, "d": {}, "e": [1, 2, 3]}', as_type=dict) != {
            "1": 3,
            "d": {},
            "e": [1, 2, 3],
        }:
            pytest.fail("convert_to dict failed for dicts.")
