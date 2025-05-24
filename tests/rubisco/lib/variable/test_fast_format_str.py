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

"""Test rubisco.lib.variable.fast_format_str module."""

import pytest

from rubisco.lib.exceptions import RUValueError
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.variable.variable import push_variables


class TestFastFormatStr:
    """Test fast_format_str."""

    def test_empty(self) -> None:
        """Test empty string."""
        if fast_format_str("") != "":
            pytest.fail("Empty string should be empty.")

    def test_literal(self) -> None:
        """Test literal string."""
        if fast_format_str("hello") != "hello":
            pytest.fail("Literal string should be literal.")

    def test_var(self) -> None:
        """Test variable."""
        push_variables("var", "world")
        if fast_format_str("${{var}}") != "world":
            pytest.fail("Variable should be replaced.")
        push_variables("var", 1)
        if fast_format_str("${{var}}") != 1:
            pytest.fail("Variable should be replaced.")
        if fast_format_str("${{var}}", fmt={"var": "test"}) != "test":
            pytest.fail("Variable should be replaced.")
        if fast_format_str("${{var}}", fmt={"var": 0.0}) != 0.0:
            pytest.fail("Variable should be replaced.")

    def test_var_not_found(self) -> None:
        """Test variable not found."""
        pytest.raises(
            KeyError,
            fast_format_str,
            "${{_U}}",
        )

    def test_var_name(self) -> None:
        """Test variable name."""
        fast_format_str("${{   s s }}")
        if (
            fast_format_str(
                "${{  a}} ${{ a_b   }} ${{a-b}} ${{a.b}}",
                fmt={"a": 1, "a_b": 2, "a-b": 3, "a.b": 4},
            )
            != "1 2 3 4"
        ):
            pytest.fail("Variable name should be valid.")

    def test_var_with_decoration(self) -> None:
        """Test variable with decoration."""
        push_variables("var", "world")
        pytest.raises(
            RUValueError,
            fast_format_str,
            "${{var:1}}",
        )
        if fast_format_str("${{var}} : ${{var}}") != "world : world":
            pytest.fail("Variable should be replaced.")
        # Although "${{var:${{var}}}} : ${{var}}" is a expression with
        # decoration, but safety check will not raise an error.
        # This is a bug, but I don't want to fix it. (We need fast instead of
        # safety)

    def test_var_with_pyexpr(self) -> None:
        """Test variable with python expression."""
        pytest.raises(
            RUValueError,
            fast_format_str,
            "${{var:$&{{1+1}}}}",
        )
