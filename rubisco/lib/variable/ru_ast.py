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

"""Rubisco variable expression AST generator."""

import enum
from dataclasses import dataclass

from rubisco.lib.variable.lexer import Token, TokenType

__all__ = ["Expression", "ExpressionType", "parse_expression"]


class ExpressionType(enum.Enum):
    """The type of the expression."""

    ROOT = 0
    CONSTANT = 1
    VARIABLE = 2
    PYTHON_EXPRESSION = 3


@dataclass
class Expression:
    """Rubisco variable expression."""

    parent: "Expression | None" = None
    children: "list[Expression] | None" = None
    type: ExpressionType = ExpressionType.CONSTANT
    value: str | None = None
    decoration: "Expression | None" = None  # Only for VARIABLE.


def _parse_expression(  # pylint: disable=R0912 # noqa: C901, PLR0912
    remain_tokens: list[Token],
    root: Expression,
) -> int:
    cur = root

    if cur.children is None:
        cur.children = []

    dont_break_if_var_end_reached = False

    idx = 0
    while idx < len(remain_tokens):
        token = remain_tokens[idx]
        if token.token_type == TokenType.CONSTANT:
            cur.children.append(
                Expression(
                    parent=cur,
                    type=ExpressionType.CONSTANT,
                    value=token.value,
                ),
            )
            idx += 1
        elif token.token_type == TokenType.VARIABLE_IDENTIFIER_START:
            # If next token is VARIABLE_NAME, it is a variable.
            # Otherwise, it must be an invalid expression.
            next_token = remain_tokens[idx + 1]
            idx += 1
            if next_token.token_type == TokenType.VARIABLE_NAME:
                var = Expression(
                    parent=cur,
                    type=ExpressionType.VARIABLE,
                    value=next_token.value,
                    decoration=None,
                )
                cur.children.append(var)
                idx += 1
                # Variable without decoration is not parsed recursively.
                # But we only break if the variable end is reached.
                dont_break_if_var_end_reached = True
            else:
                msg = "Invalid variable expression."
                raise ValueError(msg)
        elif token.token_type == TokenType.VARIABLE_DECORATE:
            # Decorate is a valid expression, so parse it recursively.
            var = cur.children[-1]
            var.decoration = Expression(parent=var, type=ExpressionType.ROOT)
            idx += 1
            idx += _parse_expression(remain_tokens[idx:], var.decoration)
        elif token.token_type == TokenType.VARIABLE_IDENTIFIER_END:
            # If end reached, return.
            idx += 1
            if not dont_break_if_var_end_reached:
                break
            dont_break_if_var_end_reached = False
        elif token.token_type == TokenType.PYTHONEXPR_IDENTIFIER_START:
            # If next token is PYTHONEXPR_EXPRESSION, it is a python expression.
            # Otherwise, it's empty python expression.
            next_token = remain_tokens[idx + 1]
            idx += 1
            if next_token.token_type == TokenType.PYTHONEXPR_EXPRESSION:
                py_expr = Expression(
                    parent=cur,
                    type=ExpressionType.PYTHON_EXPRESSION,
                    value=next_token.value,
                )
                cur.children.append(py_expr)
                idx += 1
            else:
                py_expr = Expression(
                    parent=cur,
                    type=ExpressionType.PYTHON_EXPRESSION,
                    value="",
                )
                cur.children.append(py_expr)
                idx += 1
        elif token.token_type == TokenType.PYTHONEXPR_IDENTIFIER_END:
            # It seems that the python expression is already added.
            idx += 1
        else:
            msg = "Invalid variable expression."
            raise ValueError(msg)
    return idx


def parse_expression(tokens: list[Token]) -> Expression:
    """Parse the token list to AST.

    Args:
        tokens (list[Token]): The token list.

    Returns:
        Expression: The AST.

    """
    root = Expression(
        parent=None,
        type=ExpressionType.ROOT,
        value="",
        children=[],
    )
    _parse_expression(tokens, root)

    return root
