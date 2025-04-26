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

"""Rubisco variable system."""


from typing import Any, TypeVar, cast

import pytest

from rubisco.lib.exceptions import RUValueError
from rubisco.lib.variable import to_autotype
from rubisco.lib.variable.autoformatdict import AFTypeError, AutoFormatDict
from rubisco.lib.variable.autoformatlist import AutoFormatList
from rubisco.lib.variable.builtin_vars import init_builtin_vars
from rubisco.lib.variable.callbacks import add_undefined_var_callback
from rubisco.lib.variable.format import format_str
from rubisco.lib.variable.utils import (
    assert_iter_types,
    iter_assert,
    make_pretty,
)
from rubisco.lib.variable.variable import (
    get_variable,
    pop_variables,
    push_variables,
    variables,
)

__all__ = [
    "AFTypeError",
    "AutoFormatDict",
    "AutoFormatList",
    "add_undefined_var_callback",
    "assert_iter_types",
    "format_str",
    "get_variable",
    "iter_assert",
    "make_pretty",
    "pop_variables",
    "push_variables",
    "variables",
]


T = TypeVar("T")
KT = TypeVar("KT")
VT = TypeVar("VT")


def _to_autotype(
    obj: T | list[VT] | dict[str, Any],
) -> T | AutoFormatList[VT] | AutoFormatDict:
    """Convert the list or dict object to AutoFormatList or AutoFormatDict.

    If not list or dict, return itself.
    """
    if isinstance(obj, dict) and not isinstance(obj, AutoFormatDict):
        return AutoFormatDict(obj)
    if isinstance(obj, list) and not isinstance(obj, AutoFormatList):
        return AutoFormatList(cast("list[VT]", obj))

    return cast("T", obj)


to_autotype.set_to_autotype_func(_to_autotype)


init_builtin_vars()


class TestVariable:
    """Test the variable module."""

    def _clean_variables(self) -> None:
        variables.clear()

    def test_variables(self) -> None:
        """Test the variables module."""
        self._clean_variables()
        push_variables("test", "testval")
        push_variables("test", "testval2")
        if get_variable("test") != "testval2":
            raise AssertionError
        if pop_variables("test") != "testval2":
            raise AssertionError
        if get_variable("test") != "testval":
            raise AssertionError
        if pop_variables("test") != "testval":
            raise AssertionError

    def test_format_str(self) -> None:
        """Test the format_str function."""
        self._clean_variables()
        push_variables("test", "testval")
        push_variables("test", "testval2")
        if format_str("${{test}}") != "testval2":
            raise AssertionError
        pop_variables("test")
        if format_str("${{test}}") != "testval":
            raise AssertionError
        pop_variables("test")
        pytest.raises(
            RUValueError,
            format_str,
            "${{test}}",
        )

        push_variables("test", "testval")
        if format_str("${{test}}") != "testval":
            raise AssertionError
        push_variables("test", 1)
        if format_str("${{test}}") != 1:
            raise AssertionError

        if format_str("${{test}} Test", fmt={"test": "T"}) != "T Test":
            raise AssertionError

    def test_autoformatlist(self) -> None:
        """Test the AutoFormatList class."""
        self._clean_variables()
        afl = AutoFormatList(["${{v1}}", "${{v2}}", ["${{cv1}}", "${{cv2}}"]])

        push_variables("v1", "v1val")
        push_variables("v2", "v2val")
        push_variables("cv1", "cv1val")
        push_variables("cv2", "cv2val")

        if list(afl) != ["v1val", "v2val", ["cv1val", "cv2val"]]:
            raise AssertionError

        push_variables("cv1", "cv1val")
        push_variables("cv2", "cv2val")
        if list(afl) != ["v1val", "v2val", ["cv1val", "cv2val"]]:
            raise AssertionError

        afl[0] = "${{v3}}"
        push_variables("v3", "v3val")
        if afl[0] != "v3val":
            raise AssertionError

    def test_autoformatdict_general(self) -> None:
        """Test the AutoFormatDict class."""
        self._clean_variables()
        afd = AutoFormatDict(
            {"k1": "${{v1}}", "k2": "${{v2}}", "k3": {"k4": "${{v3}}"}},
        )

        push_variables("v1", "v1val")
        push_variables("v2", "v2val")
        push_variables("v3", "v3val")
        if dict(afd) != {
            "k1": "v1val",
            "k2": "v2val",
            "k3": {"k4": "v3val"},
        }:
            raise AssertionError

        push_variables("v3", "v3val")
        if dict(afd) != {
            "k1": "v1val",
            "k2": "v2val",
            "k3": {"k4": "v3val"},
        }:
            raise AssertionError

        afd["k1"] = "${{v4}}"

        push_variables("v4", "v4val")
        if afd["k1"] != "v4val":
            raise AssertionError

        afd["k3"]["k4"] = "${{v5}}"  # type: ignore[index] # pylint: disable=E1137

        push_variables("v5", "v5val")
        if afd["k3"]["k4"] != "v5val":  # type: ignore[index] # pylint: disable=E1136
            raise AssertionError

        if list(afd.items()) != [
            ("k1", "v4val"),
            ("k2", "v2val"),
            ("k3", {"k4": "v5val"}),
        ]:
            raise AssertionError

    def test_autoformatdict_funcs(self) -> None:
        """Test the AutoFormatDict class."""
        self._clean_variables()
        afd = AutoFormatDict(
            {"k1": "${{v1}}", "k2": "${{v2}}", "k3": {"k4": "${{v3}}"}},
        )
        push_variables("v1", "v1val")
        push_variables("v2", "v2val")
        push_variables("v3", "v3val")

        if list(afd.values()) != ["v1val", "v2val", {"k4": "v3val"}]:
            raise AssertionError

        if list(afd.keys()) != ["k1", "k2", "k3"]:
            raise AssertionError

        afd["${{k6}}"] = "${{v6}}"

        push_variables("v6", "v6val")
        push_variables("k6", "k6val")
        if afd.get("${{k6}}") != "v6val" or afd["k6val"] != "v6val":
            raise AssertionError

    def test_autoformatdict_merge(self) -> None:
        """Test the AutoFormatDict class."""
        self._clean_variables()
        afd1 = AutoFormatDict(
            {"k1": "${{v1}}", "k2": "${{v2}}", "k3": {"k4": "${{v3}}"}},
        )
        afd2 = AutoFormatDict(
            {
                "k3": {"Test": "Test", "Test2": {}},
                "new": "${{new}}",
            },
        )
        push_variables("v1", "v1val")
        push_variables("v2", "v2val")
        push_variables("v3", "v3val")
        push_variables("new", "newval")
        afd1.merge(afd2)
        if afd1 != {
            "k1": "v1val",
            "k2": "v2val",
            "k3": {"k4": "v3val", "Test": "Test", "Test2": {}},
            "new": "newval",
        }:
            raise AssertionError

    def test_autoformatdict_typecheck(self) -> None:
        """Test the AutoFormatDict class."""
        self._clean_variables()
        afd = AutoFormatDict(
            {
                "k0": "${{v1}} V",
                "k1": "${{v1}}",
                "k2": "${{v2}}",
                "k3": {"k4": "${{v3}}"},
            },
        )

        push_variables("v1", 1)
        push_variables("v2", "v2val")
        push_variables("v3", value=True)
        if dict(afd) != {
            "k0": "1 V",
            "k1": 1,
            "k2": "v2val",
            "k3": {"k4": True},
        }:
            raise AssertionError

        if afd.get("k0", valtype=str | int) != "1 V":
            raise AssertionError
        if afd.get("k3", valtype=dict) != {"k4": True}:
            raise AssertionError
        pytest.raises(AFTypeError, afd.get, "k1", valtype=list)

    def test_autoformatdict_defaults(self) -> None:
        """Test the AutoFormatDict class."""
        self._clean_variables()
        afd = AutoFormatDict(
            {
                "k0": "${{v1}} V",
                "k1": "${{v1}}",
                "k2": "${{v2}}",
                "k3": {"k4": "${{v3}}"},
            },
        )
        push_variables("v1", 1)
        push_variables("v2", "v2val")
        push_variables("v3", value=True)
        if afd.get("k4", default="default") != "default":
            raise AssertionError
        if afd.get("k3", default="default") != {"k4": True}:
            raise AssertionError
        if afd.get("k3", default={}, valtype=dict) != {"k4": True}:
            raise AssertionError
