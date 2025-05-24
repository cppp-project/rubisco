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

"""Test rubisco.lib.variable module."""

import pytest

from rubisco.lib.exceptions import RUValueError
from rubisco.lib.variable.autoformatdict import AFTypeError, AutoFormatDict
from rubisco.lib.variable.autoformatlist import AutoFormatList
from rubisco.lib.variable.format import format_str
from rubisco.lib.variable.variable import (
    get_variable,
    pop_variables,
    push_variables,
    variables,
)


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
            pytest.fail("test is not set correctly.")
        if pop_variables("test") != "testval2":
            pytest.fail("test is not popped correctly.")
        if get_variable("test") != "testval":
            pytest.fail("test is not set correctly.")
        if pop_variables("test") != "testval":
            pytest.fail("test is not popped correctly.")

    def test_format_str(self) -> None:
        """Test the format_str function."""
        self._clean_variables()
        push_variables("test", "testval")
        push_variables("test", "testval2")
        if format_str("${{test}}") != "testval2":
            pytest.fail("test is not set correctly.")
        pop_variables("test")
        if format_str("${{test}}") != "testval":
            pytest.fail("test is not set correctly.")
        pop_variables("test")
        pytest.raises(
            RUValueError,
            format_str,
            "${{test}}",
        )

        push_variables("test", "testval")
        if format_str("${{test}}") != "testval":
            pytest.fail("test is not set correctly.")
        push_variables("test", 1)
        if format_str("${{test}}") != 1:
            pytest.fail("test is not set correctly.")

        if format_str("${{test}} Test", fmt={"test": "T"}) != "T Test":
            pytest.fail("test is not set correctly.")

    def test_autoformatlist(self) -> None:
        """Test the AutoFormatList class."""
        self._clean_variables()
        afl = AutoFormatList(["${{v1}}", "${{v2}}", ["${{cv1}}", "${{cv2}}"]])

        push_variables("v1", "v1val")
        push_variables("v2", "v2val")
        push_variables("cv1", "cv1val")
        push_variables("cv2", "cv2val")

        if list(afl) != ["v1val", "v2val", ["cv1val", "cv2val"]]:
            pytest.fail("Format list is not set correctly.")

        push_variables("cv1", "cv1val")
        push_variables("cv2", "cv2val")
        if list(afl) != ["v1val", "v2val", ["cv1val", "cv2val"]]:
            pytest.fail("Format list is not set correctly.")

        afl[0] = "${{v3}}"
        push_variables("v3", "v3val")
        if afl[0] != "v3val":
            pytest.fail("Format list is not set correctly.")

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
            pytest.fail("Format dict is not set correctly.")

        push_variables("v3", "v3val")
        if dict(afd) != {
            "k1": "v1val",
            "k2": "v2val",
            "k3": {"k4": "v3val"},
        }:
            pytest.fail("Format dict is not set correctly.")

        afd["k1"] = "${{v4}}"

        push_variables("v4", "v4val")
        if afd["k1"] != "v4val":
            pytest.fail("Format dict is not set correctly.")

        afd["k3"]["k4"] = "${{v5}}"  # type: ignore[index] # pylint: disable=E1137

        push_variables("v5", "v5val")
        if afd["k3"]["k4"] != "v5val":  # type: ignore[index] # pylint: disable=E1136
            pytest.fail("Format dict is not set correctly.")

        if list(afd.items()) != [
            ("k1", "v4val"),
            ("k2", "v2val"),
            ("k3", {"k4": "v5val"}),
        ]:
            pytest.fail("Format dict is not set correctly.")

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
            pytest.fail("Format dict is not set correctly.")

        if list(afd.keys()) != ["k1", "k2", "k3"]:
            pytest.fail("Format dict is not set correctly.")

        afd["${{k6}}"] = "${{v6}}"

        push_variables("v6", "v6val")
        push_variables("k6", "k6val")
        if afd.get("${{k6}}") != "v6val" or afd["k6val"] != "v6val":
            pytest.fail("Format dict is not set correctly.")

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
            pytest.fail("Format dict is not set correctly.")

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
            pytest.fail("Format dict is not set correctly.")

        if afd.get("k0", valtype=str | int) != "1 V":
            pytest.fail("Format dict is not set correctly.")
        if afd.get("k3", valtype=dict) != {"k4": True}:
            pytest.fail("Format dict is not set correctly.")
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
            pytest.fail("Format dict is not set correctly.")
        if afd.get("k3", default="default") != {"k4": True}:
            pytest.fail("Format dict is not set correctly.")
        if afd.get("k3", default={}, valtype=dict) != {"k4": True}:
            pytest.fail("Format dict is not set correctly.")
