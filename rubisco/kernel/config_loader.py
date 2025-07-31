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

"""Rubisco config file loader."""

import tomllib
from pathlib import Path
from typing import Any, TextIO

import json5 as json
import yaml

from rubisco.config import DEFAULT_CHARSET
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.variable import AutoFormatDict
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.lib.variable.utils import make_pretty

__all__ = ["SUPPORTED_EXTS", "RUConfiguration"]


def _toml_loadfunc(f: TextIO) -> dict[str, Any]:
    return tomllib.loads(f.read())


SUPPORTED_EXTS = {".json", ".json5", ".cfg", ".toml", ".ini", ".yml", ".yaml"}


class RUConfiguration(AutoFormatDict):
    """Rubisco configuration."""

    path: Path

    def __init__(self, path: Path, init: AutoFormatDict) -> None:
        """Initialize configuration.

        Args:
            path (Path): Config file path.
            init (AutoFormatDict): Initial data.

        """
        super().__init__(init)
        self.path = path

    @classmethod
    def __load_from_file(
        cls,
        path: Path,
        loaded: list[Path],
    ) -> "RUConfiguration":
        with path.open(encoding=DEFAULT_CHARSET) as f:
            if path.suffix in {".json", ".json5"}:
                loadfunc = json.load
                filetype = "JSON5"
            elif path.suffix in {".cfg", ".toml", ".ini"}:
                loadfunc = _toml_loadfunc
                filetype = "TOML"
            elif path.suffix in {".yml", ".yaml"}:
                loadfunc = yaml.safe_load
                filetype = "YAML"
            else:
                raise RUValueError(
                    fast_format_str(
                        _("Unknown file type: ${{path}}"),
                        fmt={
                            "path": make_pretty(path),
                        },
                    ),
                )

            logger.debug("Loading config file as '%s': %s", filetype, path)
            afd = RUConfiguration(path, AutoFormatDict(loadfunc(f)))
            includes: list[str] = afd.get(
                "includes",
                default=[],
                valtype=list[str],
            )
            loaded.append(path)
            for file in includes:
                fp = path.parent / file
                afd.merge(cls._load_from_file(fp, loaded))

        return afd

    @classmethod
    def _load_from_file(
        cls,
        path: Path,
        loaded: list[Path],
    ) -> "RUConfiguration":
        path = path.resolve()
        if path in loaded:
            logger.warning("Circular dependency detected: %s", path)
            return RUConfiguration(path, AutoFormatDict({}))
        afd = cls.__load_from_file(path, loaded)

        dirpath = Path(str(path) + ".d")
        if dirpath.is_dir():
            for file in dirpath.rglob("*"):
                if file.is_file():
                    afd.merge(cls.__load_from_file(file, loaded))

        return afd

    @classmethod
    def load_from_file(cls, path: Path) -> "RUConfiguration":
        """Load configuration from file.

        Args:
            path (Path): File path.

        Returns:
            RUConfiguration: The configuration.

        """
        if not path.is_file():
            for ext in SUPPORTED_EXTS:
                p = path.with_suffix(ext)
                if p.is_file():
                    return cls._load_from_file(p, [])
        return cls._load_from_file(path, [])
