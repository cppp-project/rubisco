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

"""Rubisco source package ignore file pre-processor."""

from pathlib import Path

from rubisco.config import DEFAULT_CHARSET
from rubisco.shared.api.exception import RUValueError
from rubisco.shared.api.l10n import _
from rubisco.shared.api.variable import fast_format_str, make_pretty

__all__ = ["rubiscoignore_pre_process"]


def _rubiscoignore_pre_process(file: Path, loaded_files: set[str]) -> list[str]:
    file = file.resolve()
    if file.resolve() in loaded_files:
        return []

    loaded_files.add(str(file))

    res: list[str] = []
    with file.open(encoding=DEFAULT_CHARSET) as fp:
        for line_ in fp:
            line = line_.strip()
            if line.startswith("#include "):
                _s = line.split(maxsplit=1)
                if len(_s) <= 1:
                    raise RUValueError(
                        fast_format_str(
                            _("Missing include file path in file ${{file}}."),
                            fmt={"file": make_pretty(file)},
                        ),
                    )
                _s[1] = _s[1].strip()
                res.extend(
                    _rubiscoignore_pre_process(Path(_s[1]), loaded_files),
                )
            if line.startswith("# "):
                continue
            res.append(line)
    return list(set(res))


def rubiscoignore_pre_process(file: Path) -> list[str]:
    """Read the rubiscoignore file and pre process it.

    Args:
        file (Path): the rubiscoignore file.

    Returns:
        list[str]: Processed file data.

    """
    return _rubiscoignore_pre_process(file, set())
