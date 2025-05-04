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

"""AutoFormatDict implementation."""

from collections.abc import Generator, Iterator
from os import PathLike
from types import GenericAlias, UnionType
from typing import Any, ClassVar, cast

from rubisco.lib.exceptions import RUError
from rubisco.lib.l10n import _
from rubisco.lib.variable.autoformatlist import AutoFormatList
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.variable.format import format_str
from rubisco.lib.variable.to_autotype import to_autotype
from rubisco.lib.variable.typecheck import is_instance

__all__ = ["AFTypeError", "AutoFormatDict"]


class AFTypeError(RUError, TypeError):
    """AutoFormatDict valtype error."""


class AutoFormatDict(dict[str, Any]):
    """A dictionary that can format value automatically with variables.

    We will replace all the elements which are lists or dicts to
    AutoFormatList or AutoFormatDict recursively.
    The elements will be formatted when we get them.
    Python's built-in list and dict will NEVER appear here.
    """

    raise_if_not_found: ClassVar[object] = object()

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        """Initialize the AutoFormatDict.

        Args:
            *args: The arguments to initialize the dict.
            **kwargs: The keyword arguments to initialize the dict.

        """
        super().__init__(*args, **kwargs)
        # Use orig_items to avoid undefined variable error.
        # Cauclate the variable expression later.
        for key, value in super().items():
            # Replace the value with AutoFormatList or AutoFormatDict.
            self[key] = value

    orig_get = dict[str, Any].get

    def get(  # pylint: disable=R0913
        self,
        key: str,
        default: Any = raise_if_not_found,  # noqa: ANN401
        *,
        valtype: type | GenericAlias | UnionType | None = object,
        fmt: dict[str, Any] | None = None,
    ) -> Any:  # noqa: ANN401
        """Get the value of the given key.

        Args:
            key (str): The key to get value.
            default (Any, optional): The default value to return.
                Defaults to `raise_if_not_found`.
            valtype (type | GenericAlias | UnionType | None, optional): The
                type of the value of existing key's value. If the value is not
                the same as the given type, AFTypeError will be raised. But we
                will not check the value if default value will be returned.
            fmt (dict[str, Any] | None, optional): The variable context.
                Defaults to `None`.

        Returns:
            Any: The value of the given key. If the key is not found,
                the default value will be returned.

        Raises:
            KeyError: If the key is not found.
            AFTypeError: If the value is not the same as the given type.

        """
        key = format_str(key, fmt=fmt)
        res = default
        for k in self.orig_keys():
            if format_str(k) == key:
                res = format_str(self.orig_get(k, self.raise_if_not_found))
                break

        if res is self.raise_if_not_found:
            raise KeyError(repr(key))

        if is_instance("", valtype) and isinstance(res, PathLike):
            # Treat PathLike as str.
            res = str(cast("PathLike[str]", res))

        if not is_instance(res, valtype):
            valtype_name = getattr(valtype, "__name__", repr(valtype))
            raise AFTypeError(
                fast_format_str(
                    _(
                        "The value of key ${{key}} needs to be ${{type}}"
                        " instead of ${{value_type}}.",
                    ),
                    fmt={
                        "key": repr(key),
                        "type": valtype_name,
                        "value_type": repr(type(res).__name__),
                    },
                ),
            )

        return res

    orig_keys = dict[str, Any].keys

    def keys(self) -> Generator[str]:  # type: ignore[signature-mismatch]
        """Get the keys of the dict.

        Returns:
            Generator[str]: The keys of the dict.

        """
        for key in self.orig_keys():
            yield format_str(key)

    orig_values = dict[str, Any].values

    def values(  # type: ignore[signature-mismatch]
        self,
    ) -> Generator[Any]:
        """Get the values of the dict."""
        for value in super().values():
            yield format_str(value)

    orig_items = dict[str, Any].items

    def items(  # type: ignore[signature-mismatch]
        self,
    ) -> list[tuple[str, Any]]:  # type: ignore[signature-mismatch]
        """Get the items of the dict."""
        return list(zip(list(self.keys()), list(self.values()), strict=False))

    def update(  # type: ignore[signature-mismatch]
        self,
        src: "dict[Any, Any] | AutoFormatDict | None" = None,
    ) -> None:
        """Update the dict with the given mapping.

        Args:
            src (dict | AutoFormatDict): The mapping to update.

        """
        if src is None:
            return

        if isinstance(src, dict) and not isinstance(src, AutoFormatDict):  # type: ignore[arg-type]
            src = AutoFormatDict(src)

        for key, value in src.items():
            self[key] = value

    orig_pop = dict[str, Any].pop

    def pop(  # pylint: disable=R0913
        self,
        key: str,
        default: Any = None,  # noqa: ANN401
        *,
        valtype: type | GenericAlias | UnionType | None = object,
        fmt: dict[str, Any] | None = None,
    ) -> Any:  # noqa: ANN401
        """Pop the value of the given key.

        Args:
            key (str): The key to pop value.
            default (Any): The default value to return.
            valtype (type | GenericAlias | UnionType | None): The type of the
                value of existing key's value. If the value is not the same as
                the given type, AFTypeError will be raised. But we will not
                check the value if default value will be returned.
            fmt (dict[str, Any] | None): The variable context.

        Returns:
            Any: The value of the given key.
                If the key is not found, the default value will be returned.

        Raises:
            KeyError: If the key is not found.
            AFTypeError: If the value is not the same as the given type.

        """
        res = self.get(
            key,
            default,
            valtype=valtype,
            fmt=fmt,
        )
        if key in self:
            del self[key]
        return res

    def copy(self) -> "AutoFormatDict":
        """Get a copy of the dict.

        Returns:
            AutoFormatDict: The copy of the dict.

        """
        return AutoFormatDict(self)

    def popitem(self) -> tuple[str, Any]:
        """Pop the item of the dict.

        Returns:
            tuple[str, Any]: The item of the dict.

        """
        key, value = super().popitem()
        return format_str(key), format_str(value)

    def merge(
        self,
        mapping: "dict[str, Any] | AutoFormatDict",
    ) -> None:
        """Merge the dict with the given mapping.

        Merge is a recursive operation. It can update all the values
        in the dict, including the nested dicts and lists.

        Args:
            mapping (dict[str, Any] | AutoFormatDict): The mapping to
                merge.

        """
        mapping = to_autotype()(mapping)

        for key, value in mapping.items():
            if key not in self or not isinstance(
                value,
                AutoFormatDict | AutoFormatList,
            ):
                self[key] = value
            elif isinstance(value, AutoFormatDict):
                if not isinstance(self[key], AutoFormatDict):
                    self[key] = AutoFormatDict()
                cast("AutoFormatDict", self[key]).merge(value)
            else:
                if not isinstance(self[key], AutoFormatList):
                    self[key] = AutoFormatList()
                cast("AutoFormatList[Any]", self[key]).extend(
                    cast(
                        "AutoFormatList[Any]",
                        value,
                    ),
                )

    def __setitem__(self, key: str, value: Any) -> None:  # noqa: ANN401
        """Set the value of the given key.

        Args:
            key (str): The key to set value.
            value (Any): The value to set.

        """
        super().__setitem__(key, to_autotype()(value))

    def __getitem__(
        self,
        key: str,
    ) -> "Any | AutoFormatDict | AutoFormatList[Any]":  # noqa: ANN401
        """Get the value of the given key.

        Args:
            key (str): The key to get value.

        Returns:
            Any | AutoFormatDict: The value of the given key.

        """
        return format_str(self.get(format_str(key)))

    def __iter__(self) -> Iterator[str]:
        """Get the keys iterator of the dict."""
        return self.keys()

    def __repr__(self) -> str:
        """Get the string representation of the dict.

        Returns:
            str: The string representation of the dict.

        """
        kvs = [f"{key!r}: {value!r}" for key, value in self.items()]

        return f"{{{', '.join(kvs)}}}"

    def __eq__(self, other: object) -> bool:
        """Check if the dict is equal to the other.

        Args:
            other (object): The other object to compare.

        Returns:
            bool: If the dict is equal to the other.

        """
        if not isinstance(other, dict):
            return False

        for key, value in self.items():
            if format_str(key) not in other or other[key] != value:
                return False

        return True

    def __ne__(self, other: object) -> bool:
        """Check if the dict is not equal to the other.

        Args:
            other (object): The other object to compare.

        Returns:
            bool: If the dict is not equal to the other.

        """
        return not self.__eq__(other)

    def __contains__(self, key: object) -> bool:
        """Check if the dict contains the given key.

        Args:
            key (object): The key to check.

        Returns:
            bool: If the dict contains the given key.

        """
        return any(k == format_str(key) for k in self.keys())
