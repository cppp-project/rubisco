# -*- coding: utf-8 -*-
# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2024 The C++ Plus Project.
# This file is part of the cppp-repoutils.
#
# cppp-repoutils is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# cppp-repoutils is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Load ignore file.
"""

from pathlib import Path
from typing import Callable
import gitignore_parser
from cppp_repoutils.constants import DEFAULT_IGNFILE

__all__ = ["IgnoreChecker", "load_ignore"]

IgnoreChecker = Callable[[Path], bool]


def load_ignore(directory: Path) -> IgnoreChecker:
    """Load the directory's ignore file. And ignore cppp repo always.

    Args:
        file (Path): The ignore file.

    Returns:
        IgnoreChecker: Ignore file checker.
    """

    ignlist: list[Path] = []

    for sub_dir in directory.glob("**/*"):
        if (sub_dir / DEFAULT_IGNFILE).exists():
            ignlist.append(sub_dir.relative_to(directory))

    gitign_checker = gitignore_parser.parse_gitignore(  # noqa: E501
        directory / DEFAULT_IGNFILE
    )

    def _ignore_checker(path: Path) -> bool:
        path = path.resolve()
        for ign in ignlist:  # Ignore subpackage.
            try:
                path.relative_to(directory).relative_to(ign)
                return True
            except ValueError:
                continue
        return gitign_checker(path.as_posix())

    return _ignore_checker


if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    tpath = Path(input("Path: ")).absolute()

    checker = load_ignore(tpath)

    while 1:
        try:
            print(checker(Path(input("Check: "))))
        except KeyboardInterrupt:
            break
        except Exception as exc:  # pylint: disable=broad-except
            print(type(exc).__name__, exc, sep=": ")
            print("raise?")
            if input("Y/N ") == "Y":
                raise
