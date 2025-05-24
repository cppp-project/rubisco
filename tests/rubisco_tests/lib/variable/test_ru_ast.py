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

"""Test rubisco.lib.variable.ru_ast module."""

import io
import sys
from typing import TextIO

import pytest

from rubisco.lib.variable.lexer import get_token
from rubisco.lib.variable.ru_ast import Expression, parse_expression


class TestAST:
    """Test AST."""

    def _print_ast(
        self,
        expr: Expression,
        file: TextIO,
        indent: int = 0,
    ) -> None:
        file.write(" " * indent + expr.type.name + ":\n")
        file.write(" " * (indent + 4) + "Value: " + repr(expr.value) + "\n")
        if expr.decoration:
            file.write(" " * (indent + 4) + "Decoration:" + "\n")
            self._print_ast(expr.decoration, file, indent + 8)
        if expr.children:
            file.write(" " * (indent + 4) + "Children:" + "\n")
            for child in expr.children:
                self._print_ast(child, file, indent + 8)

    def _get_ast_string(self, expr: Expression) -> str:
        file = io.StringIO()
        self._print_ast(expr, file)

        return file.getvalue()

    def _check(self, strexpr: str, expected: str) -> None:
        aststr = self._get_ast_string(parse_expression(get_token(strexpr)))
        if aststr.strip() != expected.strip():
            sys.stderr.write(aststr)
            pytest.fail("AST is not as expected.")

    def test_empty(self) -> None:
        """Test empty expression."""
        answer = """
ROOT:
    Value: ''
"""
        self._check("", answer)

    def test_nested_all(self) -> None:
        """Test nested expression."""
        expr = (
            "X${{a: ${{  Var:$&{{}}}} Hello}}Y ${{b: ${{Var}}"
            "HLWD}}}}s $&{{__import__}}"
        )
        answer = """
ROOT:
    Value: ''
    Children:
        CONSTANT:
            Value: 'X'
        VARIABLE:
            Value: 'a'
            Decoration:
                ROOT:
                    Value: None
                    Children:
                        CONSTANT:
                            Value: ' '
                        VARIABLE:
                            Value: 'Var'
                            Decoration:
                                ROOT:
                                    Value: None
                                    Children:
                                        PYTHON_EXPRESSION:
                                            Value: ''
                        CONSTANT:
                            Value: ' Hello'
                        CONSTANT:
                            Value: 'Y '
                        VARIABLE:
                            Value: 'b'
                            Decoration:
                                ROOT:
                                    Value: None
                                    Children:
                                        CONSTANT:
                                            Value: ' '
                                        VARIABLE:
                                            Value: 'Var'
                                        CONSTANT:
                                            Value: 'HLWD'
                        CONSTANT:
                            Value: '}}s '
                        PYTHON_EXPRESSION:
                            Value: '__import__'
"""
        self._check(expr, answer)
