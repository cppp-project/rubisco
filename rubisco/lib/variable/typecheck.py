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

"""Check types of variables with substitution support."""

import warnings
from types import EllipsisType, GenericAlias, NoneType, UnionType
from typing import Any, cast, get_args, get_origin

from rubisco.lib.variable.autoformatdict import AutoFormatDict
from rubisco.lib.variable.autoformatlist import AutoFormatList

__all__ = ["is_instance"]


def rubisco_isinstance(obj: Any, objtype: type | UnionType) -> bool:  # noqa: ANN401
    """Check if an object is an instance of a type.

    But treat AutoFormatList and AutoFormatDict as list and dict.

    Args:
        obj (Any): Object to check.
        objtype (type): Type to check against.

    Returns:
        bool: True if obj is an instance of objtype, False otherwise.

    """
    if objtype is AutoFormatList:
        objtype = list
    elif objtype is AutoFormatDict:
        objtype = dict

    if isinstance(obj, AutoFormatList) and objtype is list:
        return True
    if isinstance(obj, AutoFormatDict) and objtype is dict:
        return True

    return isinstance(obj, objtype)


def _is_instance_generic_alias_dict(
    obj: dict[Any, Any],
    args: tuple[Any, ...],
) -> bool:
    if len(args) != 2:  # noqa: PLR2004
        msg = "Invalid generic type"
        raise TypeError(msg)
    keytype, valtype = args
    keytype: type | GenericAlias | UnionType | None
    valtype: type | GenericAlias | UnionType | None
    return all(
        is_instance(key, keytype) and is_instance(val, valtype)
        for key, val in obj.items()
    )


def _is_instance_generic_alias_tuple(
    obj: Any,  # noqa: ANN401
    args: tuple[Any, ...],
) -> bool:
    if len(args) == 1:
        argstype = (args[0], ...)
    argstype = args

    if argstype[-1] is Ellipsis:
        argtype = args[0]
        argtype: type | GenericAlias | UnionType | None
        return all(is_instance(item, argtype) for item in obj)
    for i, argtype in enumerate(args):
        if i >= len(obj):
            break
        if not is_instance(obj[i], argtype):
            return False
    return True


def _is_instance_generic_alias(  # pylint: disable=R0911  # noqa: PLR0911
    obj: Any,  # noqa: ANN401
    objtype: GenericAlias,
) -> bool:
    orig = get_origin(objtype)
    # get_origin will return None, but type checker thinks it
    # returns a type always.
    if orig is None:  # type: ignore[arg-type]
        msg = "Invalid generic type"
        raise TypeError(msg)

    if not rubisco_isinstance(obj, orig):
        return False

    args = get_args(objtype)
    if not args:
        return True

    if orig in (list, set, AutoFormatList):
        argtype = args[0]
        argtype: type | GenericAlias | UnionType | None
        return all(is_instance(item, argtype) for item in obj)
    if orig in (dict, AutoFormatDict):
        return _is_instance_generic_alias_dict(obj, args)
    if orig is tuple:
        return _is_instance_generic_alias_tuple(obj, args)
    if orig is EllipsisType:
        # Ellipsis is a valid type for all objects.
        return True

    warnings.warn(
        f"Unsupported generic type: {orig}",
        RuntimeWarning,
        stacklevel=2,
    )
    return rubisco_isinstance(obj, orig)


def is_instance(
    obj: Any,  # noqa: ANN401
    objtype: type | GenericAlias | UnionType | None,
) -> bool:
    """Check if an object is an instance of a type or a union of types.

    Args:
        obj (Any): Object to check.
        objtype (type | GenericAlias | UnionType | None): Type or union of types
            to check against.

    """
    if objtype is None:
        return obj is None

    if get_origin(objtype) is UnionType:
        return any(is_instance(obj, t) for t in get_args(objtype))

    if rubisco_isinstance(objtype, GenericAlias):
        ot = cast("GenericAlias", objtype)
        return _is_instance_generic_alias(obj, ot)

    return rubisco_isinstance(obj, cast("type", objtype))


class TestIsInstance:
    """Test is_instance."""

    def test_single_type(self) -> None:
        """Test single type."""
        if not is_instance(1, int) or not is_instance("test", str):
            raise AssertionError
        if not is_instance(obj=True, objtype=bool):
            raise AssertionError
        if not is_instance(None, NoneType) or not is_instance(None, None):
            raise AssertionError
        if not is_instance(..., EllipsisType):
            raise AssertionError
        if (
            not is_instance({}, dict)
            or not is_instance([], list)
            or not is_instance((), tuple)
            or not is_instance(set(), set)
            or not is_instance(AutoFormatDict(), AutoFormatDict)
        ):
            raise AssertionError
        if not is_instance(AutoFormatList(), AutoFormatList):
            raise AssertionError

    def test_union_type(self) -> None:
        """Test union type."""
        if not is_instance(1, int | str):
            raise AssertionError
        if not is_instance("test", int | str):
            raise AssertionError
        if not is_instance(None, NoneType | None):
            raise AssertionError
        if not is_instance(..., EllipsisType | None):
            raise AssertionError

    def test_generic_alias(self) -> None:
        """Test generic alias."""
        if not is_instance([1, 2, 3], list[int]):
            raise AssertionError
        if is_instance((1, 2, 3), list[int]):
            raise AssertionError
        if is_instance([1, 2, 3], list[str]):
            raise AssertionError
        if not is_instance([1, 2, 3], list[int | str]):
            raise AssertionError
        if not is_instance([1, "", "", None, 1, 5], list[int | str | None]):
            raise AssertionError
        if not is_instance((1, 2, 3), tuple[int]) or not is_instance(
            (1, 2, 3),
            tuple[int, ...],
        ):
            raise AssertionError
        if (
            not is_instance((1, 2, 3), tuple[int | str])
            or not is_instance((1, 2, 3), tuple)
            or not is_instance((1, 2, 3), tuple[int, int, int])
            or not is_instance((1, 2, 3), tuple[int])
            or is_instance((1, 2, 3), tuple[int, str, str | int])
        ):
            raise AssertionError

    def test_generic_alias_dict(self) -> None:
        """Test generic alias dict."""
        if not is_instance({}, dict[str, str]):
            raise AssertionError
        if not is_instance({"a": "b"}, dict[str, str]):
            raise AssertionError
        if not is_instance({"a": 1}, dict[str, int]):
            raise AssertionError
        if not is_instance({"a": 1}, dict[str, int | str]):
            raise AssertionError
        if not is_instance({"a": 1, "b": "c"}, dict[str, int | str]):
            raise AssertionError
        if not is_instance({"a": 1, "b": None}, dict[str, int | None]):
            raise AssertionError
        if not is_instance(
            {"a": 1, "b": None},
            AutoFormatDict[str, int | None],
        ):
            raise AssertionError

    def test_nested(self) -> None:
        """Test nested."""
        if not is_instance(
            {"a": {"b": 1}},
            dict[str, dict[str, int]],
        ):
            raise AssertionError
        if is_instance(
            {"a": {"b": 1}},
            dict[str, dict[str, str]],
        ):
            raise AssertionError
        if not is_instance(
            {"a": {"b": [(1, 2, 3), None]}, "c": 1},
            dict[str, dict[str, list[tuple[int, ...] | None]] | int],
        ):
            raise AssertionError
        if is_instance(
            {"a": {"b": [(1, 2, 3), None]}, "c": 1},
            dict[str, dict[str, list[tuple[int, str] | None]] | int],
        ):
            raise AssertionError
