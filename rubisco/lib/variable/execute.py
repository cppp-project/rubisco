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

"""Execute Rubisco variable expression."""

from typing import Any

import pytest

from rubisco.lib.exceptions import RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.variable.callbacks import on_undefined_var
from rubisco.lib.variable.lexer import get_token
from rubisco.lib.variable.pyexpr_sandbox import eval_pyexpr
from rubisco.lib.variable.ru_ast import (
    Expression,
    ExpressionType,
    parse_expression,
)
from rubisco.lib.variable.variable import (
    get_variable,
    has_variable,
    push_variables,
)

__all__ = ["execute_expression"]


def _exec_variable_type(expr: Expression) -> str | Any:  # noqa: ANN401
    if expr.value is None:
        msg = "Variable's value is None."
        raise ValueError(msg)
    if has_variable(expr.value):
        return get_variable(expr.value)

    on_undefined_var(expr.value)

    if expr.decoration:
        return execute_expression(expr.decoration)

    raise RUValueError(
        _("Undefined variable: ${{var}}").replace("${{var}}", expr.value),
    )


def execute_expression(expr: Expression) -> str | Any:  # noqa: ANN401
    """Execute the expression.

    Args:
        expr (Expression): The expression to execute.

    Returns:
        str | Any: The result of the execution.
            If the expression only contains a variable, the result will not
            be converted to a string.

    """
    if expr.type == ExpressionType.ROOT:
        if expr.children is None:
            return ""
        if len(expr.children) == 1:
            return execute_expression(expr.children[0])
        res = ""
        for child in expr.children:
            res += str(execute_expression(child))
        return res
    if expr.type == ExpressionType.CONSTANT:
        return expr.value
    if expr.type == ExpressionType.VARIABLE:
        return _exec_variable_type(expr)
    if expr.type == ExpressionType.PYTHON_EXPRESSION:
        if expr.value is None:
            msg = "Python expression's value is None."
            raise ValueError(msg)
        return eval_pyexpr(expr.value)

    msg = f"Unknown expression type: {expr.type}"
    raise ValueError(msg)


class TestExecuteExpression:
    """Test execute_expression."""

    def _check(self, expr: str, res: str | Any) -> None:  # noqa: ANN401
        expr_result = execute_expression(parse_expression(get_token(expr)))
        if expr_result != res:
            raise AssertionError

    def test_empty(self) -> None:
        """Test empty expression."""
        self._check("", "")

    def test_root(self) -> None:
        """Test root expression."""
        self._check("a", "a")

    def test_variable(self) -> None:
        """Test variable expression."""
        push_variables("a", "b")
        self._check("${{a}}", "b")
        push_variables("a", 1)
        self._check("${{a}}", 1)

    def test_var_decoration(self) -> None:
        """Test variable decoration."""
        self._check("${{_U: c}}", " c")
        push_variables("a", "b")
        self._check("${{_U:${{_U:${{a}}}}}}", "b")

    def test_pyexpr(self) -> None:
        """Test python expression."""
        self._check("$&{{1+1}}", 2)
        push_variables("a", 1)
        self._check("$&{{a+1}}", 2)

    def test_nested_all(self) -> None:
        """Test nested all."""
        push_variables("a", None)
        expr = (
            "X${{aa: ${{  Var:$&{{a}}}} Hello}}Y ${{bb: ${{a}}"  # Don't remove.
            "HLWD}}}}s $&{{None}}"
        )
        self._check(expr, "X None HelloY  NoneHLWD}}s None")

    def test_undefined_var(self) -> None:
        """Test undefined variable."""
        pytest.raises(RUValueError, self._check, "${{_U}}", "")
