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

"""Convert the object to AutoFormatList or AutoFormatDict recursively.

This is only a placeholder. It will be implemented in `__init__.py`.
"""

from collections.abc import Callable
from typing import Any

__all__ = ["set_to_autotype_func", "to_autotype"]


to_autotype_func: Callable[[Any], Any]


def to_autotype() -> Callable[[Any], Any]:
    """Get the to_autotype function.

    Returns:
        Callable[[Any], Any]: The to_autotype function.

    """
    return to_autotype_func


def set_to_autotype_func(func: Callable[[Any], Any]) -> None:
    """Set the to_autotype function.

    Args:
        func (Callable): The to_autotype function.

    """
    global to_autotype_func  # pylint: disable=W0603  # noqa: PLW0603
    to_autotype_func = func


def _to_autotype(obj: Any) -> Any:  # noqa: ANN401
    raise NotImplementedError


set_to_autotype_func(_to_autotype)
