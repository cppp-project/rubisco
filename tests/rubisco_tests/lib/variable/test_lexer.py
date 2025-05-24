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

"""Test rubisco.lib.variable.lexer module."""

import pytest

from rubisco.lib.exceptions import RUValueError
from rubisco.lib.variable.lexer import Token, TokenType, get_token


class TestLexer:
    """Test lexer."""

    def test_empty(self) -> None:
        """Test empty string."""
        if get_token(""):
            pytest.fail("Empty string should return empty list.")

    def test_constant(self) -> None:
        """Test constant."""
        if get_token("hello world") != [
            Token(TokenType.CONSTANT, "hello world"),
        ]:
            pytest.fail("Constant should return constant token.")

    def test_variable(self) -> None:
        """Test variable."""
        if get_token("${{hello}}") != [
            Token(TokenType.VARIABLE_IDENTIFIER_START),
            Token(TokenType.VARIABLE_NAME, "hello"),
            Token(TokenType.VARIABLE_IDENTIFIER_END),
        ]:
            pytest.fail("Variable should return variable token.")

    def test_variable_with_default(self) -> None:
        """Test variable with default."""
        if get_token("${{hello: world}}") != [
            Token(TokenType.VARIABLE_IDENTIFIER_START),
            Token(TokenType.VARIABLE_NAME, "hello"),
            Token(TokenType.VARIABLE_DECORATE),
            Token(TokenType.CONSTANT, " world"),
            Token(TokenType.VARIABLE_IDENTIFIER_END),
        ]:
            pytest.fail("Variable with default should return variable token.")

    def test_variable_with_default_and_space(self) -> None:
        """Test variable with default with space in variable name."""
        if get_token("${{  hello  : world}}") != [
            Token(TokenType.VARIABLE_IDENTIFIER_START),
            Token(TokenType.VARIABLE_NAME, "hello"),
            Token(TokenType.VARIABLE_DECORATE),
            Token(TokenType.CONSTANT, " world"),
            Token(TokenType.VARIABLE_IDENTIFIER_END),
        ]:
            pytest.fail("Variable with default should return variable token.")

    def test_mixed(self) -> None:
        """Test mixed."""
        if get_token("hello ${{world}} world") != [
            Token(TokenType.CONSTANT, "hello "),
            Token(TokenType.VARIABLE_IDENTIFIER_START),
            Token(TokenType.VARIABLE_NAME, "world"),
            Token(TokenType.VARIABLE_IDENTIFIER_END),
            Token(TokenType.CONSTANT, " world"),
        ]:
            pytest.fail("Mixed should return mixed token.")

    def test_mixed_with_default(self) -> None:
        """Test mixed with default."""
        if get_token("hello ${{world: default}} world ${{a}}") != [
            Token(TokenType.CONSTANT, "hello "),
            Token(TokenType.VARIABLE_IDENTIFIER_START),
            Token(TokenType.VARIABLE_NAME, "world"),
            Token(TokenType.VARIABLE_DECORATE),
            Token(TokenType.CONSTANT, " default"),
            Token(TokenType.VARIABLE_IDENTIFIER_END),
            Token(TokenType.CONSTANT, " world "),
            Token(TokenType.VARIABLE_IDENTIFIER_START),
            Token(TokenType.VARIABLE_NAME, "a"),
            Token(TokenType.VARIABLE_IDENTIFIER_END),
        ]:
            pytest.fail("Mixed with default should return mixed token.")

    def test_pythonexpr(self) -> None:
        """Test python expression."""
        if get_token("$&{{hello}}") != [
            Token(TokenType.PYTHONEXPR_IDENTIFIER_START),
            Token(TokenType.PYTHONEXPR_EXPRESSION, "hello"),
            Token(TokenType.PYTHONEXPR_IDENTIFIER_END),
        ]:
            pytest.fail(
                "Python expression should return python expression token.",
            )

    def test_nested_variable(self) -> None:
        """Test nested variable."""
        if get_token("srt ${{hello: ${{world}}}} end") != [
            Token(TokenType.CONSTANT, "srt "),
            Token(TokenType.VARIABLE_IDENTIFIER_START),
            Token(TokenType.VARIABLE_NAME, "hello"),
            Token(TokenType.VARIABLE_DECORATE),
            Token(TokenType.CONSTANT, " "),
            Token(TokenType.VARIABLE_IDENTIFIER_START),
            Token(TokenType.VARIABLE_NAME, "world"),
            Token(TokenType.VARIABLE_IDENTIFIER_END),
            Token(TokenType.VARIABLE_IDENTIFIER_END),
            Token(TokenType.CONSTANT, " end"),
        ]:
            pytest.fail("Nested variable should return nested variable token.")

        if get_token("srt ${{hello: ${{ world:${{a}}}}}} end") != [
            Token(TokenType.CONSTANT, "srt "),
            Token(TokenType.VARIABLE_IDENTIFIER_START),
            Token(TokenType.VARIABLE_NAME, "hello"),
            Token(TokenType.VARIABLE_DECORATE),
            Token(TokenType.CONSTANT, " "),
            Token(TokenType.VARIABLE_IDENTIFIER_START),
            Token(TokenType.VARIABLE_NAME, "world"),
            Token(TokenType.VARIABLE_DECORATE),
            Token(TokenType.VARIABLE_IDENTIFIER_START),
            Token(TokenType.VARIABLE_NAME, "a"),
            Token(TokenType.VARIABLE_IDENTIFIER_END),
            Token(TokenType.VARIABLE_IDENTIFIER_END),
            Token(TokenType.VARIABLE_IDENTIFIER_END),
            Token(TokenType.CONSTANT, " end"),
        ]:
            pytest.fail("Nested variable should return nested variable token.")

        # Notice: This is a constant, not end identifier.
        #                            v
        if get_token("srt ${{hello }}}} end") != [
            Token(TokenType.CONSTANT, "srt "),
            Token(TokenType.VARIABLE_IDENTIFIER_START),
            Token(TokenType.VARIABLE_NAME, "hello"),
            Token(TokenType.VARIABLE_IDENTIFIER_END),
            Token(TokenType.CONSTANT, "}} end"),
        ]:
            pytest.fail("Nested variable should return nested variable token.")

        #                             v
        if get_token("srt ${{hello:x}}}} end") != [
            Token(TokenType.CONSTANT, "srt "),
            Token(TokenType.VARIABLE_IDENTIFIER_START),
            Token(TokenType.VARIABLE_NAME, "hello"),
            Token(TokenType.VARIABLE_DECORATE),
            Token(TokenType.CONSTANT, "x"),
            Token(TokenType.VARIABLE_IDENTIFIER_END),
            Token(TokenType.CONSTANT, "}} end"),
        ]:
            pytest.fail("Nested variable should return nested variable token.")

    def test_nested_all(self) -> None:
        """Test nested all."""
        fmt = (
            "X${{a: ${{  Var:$&{{}}}} Hello}}Y ${{b: ${{Var}}"
            "HLWD}}}}s $&{{__import__}}"
        )
        tokens = get_token(fmt)
        if tokens != [
            Token(TokenType.CONSTANT, "X"),
            Token(TokenType.VARIABLE_IDENTIFIER_START),
            Token(TokenType.VARIABLE_NAME, "a"),
            Token(TokenType.VARIABLE_DECORATE),
            Token(TokenType.CONSTANT, " "),
            Token(TokenType.VARIABLE_IDENTIFIER_START),
            Token(TokenType.VARIABLE_NAME, "Var"),
            Token(TokenType.VARIABLE_DECORATE),
            Token(TokenType.PYTHONEXPR_IDENTIFIER_START),
            Token(TokenType.PYTHONEXPR_IDENTIFIER_END),
            Token(TokenType.VARIABLE_IDENTIFIER_END),
            Token(TokenType.CONSTANT, " Hello"),
            Token(TokenType.VARIABLE_IDENTIFIER_END),
            Token(TokenType.CONSTANT, "Y "),
            Token(TokenType.VARIABLE_IDENTIFIER_START),
            Token(TokenType.VARIABLE_NAME, "b"),
            Token(TokenType.VARIABLE_DECORATE),
            Token(TokenType.CONSTANT, " "),
            Token(TokenType.VARIABLE_IDENTIFIER_START),
            Token(TokenType.VARIABLE_NAME, "Var"),
            Token(TokenType.VARIABLE_IDENTIFIER_END),
            Token(TokenType.CONSTANT, "HLWD"),
            Token(TokenType.VARIABLE_IDENTIFIER_END),
            Token(TokenType.CONSTANT, "}}s "),
            Token(TokenType.PYTHONEXPR_IDENTIFIER_START),
            Token(TokenType.PYTHONEXPR_EXPRESSION, "__import__"),
            Token(TokenType.PYTHONEXPR_IDENTIFIER_END),
        ]:
            pytest.fail("Nested all should return nested all token.")

    def test_invalid(self) -> None:
        """Test invalid."""
        pytest.raises(
            RUValueError,
            get_token,
            "hello ${{world",
        )
        pytest.raises(
            RUValueError,
            get_token,
            "hello ${{world:}}",
        )
        pytest.raises(
            RUValueError,
            get_token,
            "hello ${{world: ${{a}}",
        )
        pytest.raises(
            RUValueError,
            get_token,
            "hello ${{",
        )
