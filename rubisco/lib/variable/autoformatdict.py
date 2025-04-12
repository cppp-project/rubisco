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

from collections.abc import Generator, Iterable, Iterator
from types import GenericAlias, UnionType
from typing import Any, Generic, Self, TypeVar, overload

from rubisco.lib.l10n import _
from rubisco.lib.variable.autoformatlist import AutoFormatList
from rubisco.lib.variable.format import format_str
from rubisco.lib.variable.to_autotype import to_autotype

__all__ = ["AFTypeError", "AutoFormatDict"]


class AFTypeError(TypeError):
    """AutoFormatDict valtype error."""


KT = TypeVar("KT")
VT = TypeVar("VT")


class AutoFormatDict(dict[KT, VT], Generic[KT, VT]):
    """A dictionary that can format value automatically with variables.

    We will replace all the elements which are lists or dicts to
    AutoFormatList or AutoFormatDict recursively.
    The elements will be formatted when we get them.
    Python's built-in list and dict will NEVER appear here.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        """Initialize the AutoFormatDict.

        Args:
            *args: The arguments to initialize the dict.
            **kwargs: The keyword arguments to initialize the dict.

        """
        super().__init__(*args, **kwargs)
        # Use orig_items to avoid undefined variable error.
        # Cauclate the variable expression later.
        for key, value in self.orig_items():
            # Replace the value with AutoFormatList or AutoFormatDict.
            self[key] = value

    orig_get = dict[KT, VT].get

    @overload  # type: ignore[override]
    def get(self, key: KT, default: None = None, /) -> VT | None: ...
    @overload
    def get(self, key: KT, default: VT, /) -> VT: ...

    @overload
    def get(self, key: KT) -> VT: ...

    @overload
    def get(
        self,
        key: KT,
        valtype: type | GenericAlias | UnionType | None,
    ) -> VT: ...

    @overload
    def get(self, key: KT, default: VT) -> VT: ...

    @overload
    def get(
        self,
        key: KT,
        default: VT,
        valtype: type | GenericAlias | UnionType | None,
    ) -> VT: ...

    def get(  # type: ignore[signature-mismatch]
        self,
        key: KT,
        *args: VT | object,
        **kwargs: Any,
    ) -> VT | None:
        """Get the value of the given key.

        Args:
            key (str): The key to get value.
            *args: The arguments to get value.
            **kwargs: The keyword arguments to get value.

        Raises:
            KeyError: If the key is not found.
            AFTypeError: If the value is not the same as the given type.

        Returns:
            Any: The value of the given key.

        """
        valtype = kwargs.pop("valtype", object)
        if valtype == AutoFormatDict:
            valtype = dict
        elif valtype == AutoFormatList:
            valtype = list
        if len(args) == 1:
            res = format_str(self.orig_get(format_str(key), args[0]))
        elif "default" in kwargs:
            res = format_str(
                self.orig_get(format_str(key), kwargs["default"]),
            )
        else:
            key = format_str(key)
            if key not in self:
                raise KeyError(repr(key))
            res = None
            for key2, val in self.items():
                if format_str(key2) == key:
                    res = val
                    break
        if not isinstance(res, valtype):
            if hasattr(valtype, "__name__"):
                valtype_name = valtype.__name__
            else:
                valtype_name = f"'{valtype}'"
            raise AFTypeError(
                format_str(
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

    orig_keys = dict.keys

    def keys(
        self,
    ) -> Generator[str, None, None]:  # type: ignore[signature-mismatch]
        """Get the keys of the dict."""
        for key in super().keys():  # noqa: SIM118
            yield format_str(key)

    orig_values = dict.values

    def values(
        self,
    ) -> Generator[Any, None, None]:  # type: ignore[signature-mismatch]
        """Get the values of the dict."""
        for value in super().values():
            yield format_str(value)

    orig_items = dict.items

    def items(
        self,
    ) -> list[tuple[str, VT]]:  # type: ignore[signature-mismatch]
        """Get the items of the dict."""
        return list(zip(list(self.keys()), list(self.values()), strict=False))

    def update(self, src: "dict | AutoFormatDict | None" = None) -> None:
        """Update the dict with the given mapping.

        Args:
            src (dict | AutoFormatDict): The mapping to update.

        """
        if src is None:
            return

        if isinstance(src, dict) and not isinstance(src, AutoFormatDict):
            src = AutoFormatDict(src)

        for key, value in src.items():
            self[key] = value

    orig_pop = dict.pop

    @overload
    def pop(self, key: str) -> Any: ...  # noqa: ANN401

    @overload
    def pop(self, key: str, default: Any) -> Any:  # noqa: ANN401
        ...

    def pop(self, key: str, *args: Any, **kwargs: Any) -> Any:
        """Pop the value of the given key.

        Args:
            key (str): The key to pop value.
            *args: The arguments to pop value.
            **kwargs: The keyword arguments to pop value.

        Returns:
            Any: The value of the given key.

        """
        if len(args) == 1:
            res = format_str(super().pop(format_str(key), args[0]))
        elif "default" in kwargs:
            res = format_str(
                super().pop(format_str(key), kwargs["default"]),
            )
        else:
            res = format_str(super().pop(format_str(key)))
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

    def merge(self, mapping: dict[KT, VT] | Self) -> None:
        """Merge the dict with the given mapping.

        Merge is a recursive operation. It can update all the values
        in the dict, including the nested dicts and lists.

        Args:
            mapping (dict | AutoFormatDict): The mapping to merge.

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
                self[key].merge(value)
            else:  # AutoFormatList
                if not isinstance(self[key], AutoFormatList):
                    self[key] = AutoFormatList()
                self[key].extend(value)

    def __setitem__(self, key: KT, value: VT) -> None:
        """Set the value of the given key.

        Args:
            key (KT): The key to set value.
            value (VT): The value to set.

        """
        super().__setitem__(key, to_autotype()(value))

    def __getitem__(self, key: str) -> Any:  # noqa: ANN401
        """Get the value of the given key.

        Args:
            key (str): The key to get value.

        Returns:
            Any: The value of the given key.

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
            if key not in other or other[key] != value:
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

    @classmethod
    def fromkeys(
        cls,
        keys: Iterable,
        value: Any = None,  # noqa: ANN401
    ) -> "AutoFormatDict":
        """Create a new dict with the given keys and value.

        Args:
            keys (Iterable): The keys to create the dict.
            value (Any, optional): The value to create the dict. Defaults to
                None.

        Returns:
            AutoFormatDict: The new dict.

        """
        return cls(dict.fromkeys(keys, value))
