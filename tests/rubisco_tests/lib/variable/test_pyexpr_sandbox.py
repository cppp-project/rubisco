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

"""Test rubisco.lib.variable.pyexpr_sandbox module."""


import pytest

from rubisco.lib.variable.pyexpr_sandbox import (
    RUEvalError,
    RUFunctionDisallowedError,
    eval_pyexpr,
)


class TestEval:
    """Test eval_pyexpr."""

    def test_eval(self) -> None:
        """Test eval."""
        if eval_pyexpr("1 + 1") != 2:  # noqa: PLR2004
            pytest.fail("1 + 1 != 2")
        if eval_pyexpr('"str" * 2') != "strstr":
            pytest.fail('"str" * 2 != "strstr"')

    def test_syntax_error(self) -> None:
        """Test syntax error."""
        pytest.raises(
            RUEvalError,
            eval_pyexpr,
            "",
        )

        pytest.raises(
            RUEvalError,
            eval_pyexpr,
            "+",
        )

    def test_disallowed_function(self) -> None:
        """Test disallowed function."""
        pytest.raises(
            RUFunctionDisallowedError,
            eval_pyexpr,
            "__import__('os')",
        )
        pytest.raises(
            RUFunctionDisallowedError,
            eval_pyexpr,
            "open('test.txt')",
        )
        pytest.raises(
            RUFunctionDisallowedError,
            eval_pyexpr,
            'exec(\'__import__("o" + "s")\')',
        )
