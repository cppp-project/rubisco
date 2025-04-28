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

"""Parse the expression to tokens list."""

import enum
import re
from dataclasses import dataclass

import pytest

from rubisco.lib.exceptions import RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.stack import Stack

__all__ = ["Token", "TokenType", "get_token"]


class TokenType(enum.Enum):
    """The type of the token."""

    CONSTANT = 0
    VARIABLE_IDENTIFIER_START = 1
    VARIABLE_NAME = 2
    VARIABLE_DECORATE = 3
    VARIABLE_IDENTIFIER_END = 4
    PYTHONEXPR_IDENTIFIER_START = 5
    PYTHONEXPR_EXPRESSION = 6
    PYTHONEXPR_IDENTIFIER_END = 7


@dataclass
class Token:
    """The token of the expression."""

    token_type: TokenType
    value: str = ""


class TS(enum.Enum):
    """The state of the lexer."""

    CONSTANT = 0
    VARIABLE_IDENTIFIER_START = 1  # ${{
    VARIABLE_NAME = 4  # ${<name>}}
    VARIABLE_DECORATE = 5  # :
    DECORATE_CONSTANT = 6  # :<constant>}}. This constant don't support "}}"
    PYTHONEXPR_IDENTIFIER_START = 8  # $&{{
    PYTHONEXPR_EXPRESSION = 9  # <expression>


def get_token(  # pylint: disable=R0912, R0915 # noqa: C901, PLR0912, PLR0915
    expression: str,
) -> list[Token]:
    """Get the token list of the expression.

    Args:
        expression (str): The expression to parse.

    Returns:
        list[Token]: The token list of the expression.

    """
    current_state: Stack[TS] = Stack()
    current_state.put(TS.CONSTANT)
    cur_token_value = ""
    cur_ignored_token_value = ""

    res: list[Token] = []

    idx = 0

    def _read(size: int) -> str:
        nonlocal idx
        res = expression[idx : idx + size]
        idx += size
        return res

    def _flush(tt: TokenType) -> None:
        nonlocal cur_token_value
        if cur_token_value:
            res.append(
                Token(
                    tt,
                    cur_token_value,
                ),
            )
            cur_token_value = ""

    def _push(tt: TokenType) -> None:
        nonlocal cur_token_value
        res.append(
            Token(
                tt,
                cur_token_value,
            ),
        )
        cur_token_value = ""

    while idx < len(expression):
        c = _read(1)
        if current_state.top() in (
            TS.CONSTANT,
            TS.DECORATE_CONSTANT,
        ):
            dont_save_char = False
            if c == "}" and current_state.top() == TS.DECORATE_CONSTANT:
                if _read(1) != "}":
                    msg = _("Invalid variable expression.")
                    raise RUValueError(msg)
                _flush(TokenType.CONSTANT)
                current_state.get()  # Pop DECORATE_CONSTANT.
                current_state.get()  # Pop VARIABLE_DECORATE.
                current_state.get()  # Pop VARIABLE_IDENTIFIER_START
                _push(TokenType.VARIABLE_IDENTIFIER_END)
                dont_save_char = True

            if c == "$":
                cur_ignored_token_value += c
                next_str = _read(2)
                cur_ignored_token_value += next_str
                if next_str == "{{":
                    _flush(TokenType.CONSTANT)
                    current_state.put(TS.VARIABLE_IDENTIFIER_START)
                    _push(TokenType.VARIABLE_IDENTIFIER_START)
                    cur_ignored_token_value = ""
                    current_state.put(TS.VARIABLE_NAME)
                elif next_str == "&{":
                    next_c = _read(1)
                    cur_ignored_token_value += next_c
                    if next_c == "{":
                        _flush(TokenType.CONSTANT)
                        current_state.put(TS.PYTHONEXPR_IDENTIFIER_START)
                        _push(TokenType.PYTHONEXPR_IDENTIFIER_START)
                        cur_ignored_token_value = ""
                        current_state.put(TS.PYTHONEXPR_EXPRESSION)
                else:
                    cur_token_value += cur_ignored_token_value
            elif not dont_save_char:
                cur_token_value += c
        elif current_state.top() == TS.VARIABLE_NAME:
            if c == ":":
                _flush(TokenType.VARIABLE_NAME)
                current_state.get()  # Pop VARIABLE_NAME.
                current_state.put(TS.VARIABLE_DECORATE)
            elif c == "}":
                if _read(1) != "}":
                    msg = _("Invalid variable expression.")
                    raise RUValueError(msg)
                _flush(TokenType.VARIABLE_NAME)
                _push(TokenType.VARIABLE_IDENTIFIER_END)
                current_state.get()  # Pop VARIABLE_NAME.
                current_state.get()  # Pop VARIABLE_IDENTIFIER_START
            else:
                cur_token_value += c
        elif current_state.top() == TS.PYTHONEXPR_EXPRESSION:
            if c == "}":
                cur_ignored_token_value += c
                next_c = _read(1)
                cur_ignored_token_value += next_c
                if next_c == "}":
                    # The expression is ended.
                    _flush(TokenType.PYTHONEXPR_EXPRESSION)
                    current_state.get()  # Pop PYTHONEXPR_EXPRESSION.
                    current_state.get()  # Pop PYTHONEXPR_IDENTIFIER_START
                    _push(TokenType.PYTHONEXPR_IDENTIFIER_END)
                else:
                    cur_token_value += cur_ignored_token_value
                    cur_ignored_token_value = ""
            else:
                cur_token_value += c
        elif current_state.top() == TS.VARIABLE_DECORATE:
            idx -= 1  # Unget possible '$'.
            if c in (":", "}"):
                msg = _("Invalid variable decorate expression.")
                raise RUValueError(msg)
            _push(TokenType.VARIABLE_DECORATE)
            current_state.put(TS.DECORATE_CONSTANT)
        else:
            msg = f"Unknown state: {current_state}"
            raise ValueError(msg)

    if cur_token_value:
        res.append(
            Token(
                TokenType.CONSTANT,
                cur_token_value,
            ),
        )

    if current_state.get() != TS.CONSTANT or not current_state.empty():
        msg = _("Invalid variable expression.")
        raise RUValueError(msg)

    for token in res:
        if token.token_type == TokenType.VARIABLE_NAME:
            token.value = token.value.strip()
            if not re.match(r"^[a-zA-Z0-9_.-]*$", token.value):
                msg = _("Invalid variable name.")
                raise RUValueError(
                    msg,
                    hint=_(
                        "Variable name must only contain letters,"
                        " numbers, and '-', '.', '_'.",
                    ),
                )

    return res


class TestLexer:
    """Test lexer."""

    def test_empty(self) -> None:
        """Test empty string."""
        if get_token(""):
            raise AssertionError

    def test_constant(self) -> None:
        """Test constant."""
        if get_token("hello world") != [
            Token(TokenType.CONSTANT, "hello world"),
        ]:
            raise AssertionError

    def test_variable(self) -> None:
        """Test variable."""
        if get_token("${{hello}}") != [
            Token(TokenType.VARIABLE_IDENTIFIER_START),
            Token(TokenType.VARIABLE_NAME, "hello"),
            Token(TokenType.VARIABLE_IDENTIFIER_END),
        ]:
            raise AssertionError

    def test_variable_with_default(self) -> None:
        """Test variable with default."""
        if get_token("${{hello: world}}") != [
            Token(TokenType.VARIABLE_IDENTIFIER_START),
            Token(TokenType.VARIABLE_NAME, "hello"),
            Token(TokenType.VARIABLE_DECORATE),
            Token(TokenType.CONSTANT, " world"),
            Token(TokenType.VARIABLE_IDENTIFIER_END),
        ]:
            raise AssertionError

    def test_variable_with_default_and_space(self) -> None:
        """Test variable with default with space in variable name."""
        if get_token("${{  hello  : world}}") != [
            Token(TokenType.VARIABLE_IDENTIFIER_START),
            Token(TokenType.VARIABLE_NAME, "hello"),
            Token(TokenType.VARIABLE_DECORATE),
            Token(TokenType.CONSTANT, " world"),
            Token(TokenType.VARIABLE_IDENTIFIER_END),
        ]:
            raise AssertionError

    def test_mixed(self) -> None:
        """Test mixed."""
        if get_token("hello ${{world}} world") != [
            Token(TokenType.CONSTANT, "hello "),
            Token(TokenType.VARIABLE_IDENTIFIER_START),
            Token(TokenType.VARIABLE_NAME, "world"),
            Token(TokenType.VARIABLE_IDENTIFIER_END),
            Token(TokenType.CONSTANT, " world"),
        ]:
            raise AssertionError

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
            raise AssertionError

    def test_pythonexpr(self) -> None:
        """Test python expression."""
        if get_token("$&{{hello}}") != [
            Token(TokenType.PYTHONEXPR_IDENTIFIER_START),
            Token(TokenType.PYTHONEXPR_EXPRESSION, "hello"),
            Token(TokenType.PYTHONEXPR_IDENTIFIER_END),
        ]:
            raise AssertionError

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
            raise AssertionError

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
            raise AssertionError

        # Notice: This is a constant, not end identifier.
        #                            v
        if get_token("srt ${{hello }}}} end") != [
            Token(TokenType.CONSTANT, "srt "),
            Token(TokenType.VARIABLE_IDENTIFIER_START),
            Token(TokenType.VARIABLE_NAME, "hello"),
            Token(TokenType.VARIABLE_IDENTIFIER_END),
            Token(TokenType.CONSTANT, "}} end"),
        ]:
            raise AssertionError

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
            raise AssertionError

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
            raise AssertionError

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
