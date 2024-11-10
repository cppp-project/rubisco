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

"""Package management utils for environment."""

from __future__ import annotations

import contextlib
import re
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import json5

from rubisco.config import DEFAULT_CHARSET, EXTENSIONS_DIR
from rubisco.envutils.pip import install_requirements
from rubisco.lib.archive import extract_zip
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.fileutil import TemporaryObject
from rubisco.lib.l10n import _
from rubisco.lib.variable import (
    AutoFormatDict,
    assert_iter_types,
    format_str,
    iter_assert,
)
from rubisco.lib.version import Version
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

if TYPE_CHECKING:
    from rubisco.envutils.env import RUEnvironment


@dataclass
class ExtensionPackageInfo:  # pylint: disable=too-many-instance-attributes
    """Extension package info."""

    name: str
    version: Version
    description: str
    homepage: str
    maintainers: list[str]
    pkg_license: str
    tags: list[str]
    requirements: str | None


def _pkg_check(zip_file: zipfile.ZipFile, pkg_name: str) -> None:
    files = zip_file.namelist()
    root_list = set()
    for file in files:
        if Path(file).parts:
            root_list.add(str(Path(file).parts[0]))

    try:
        root_list.remove(pkg_name)
        root_list.remove("rubisco.json")
    except KeyError as exc:
        raise RUValueError(
            format_str(
                _(
                    "'${{name}}' package must contain a directory with the "
                    "same name as the package name and a 'rubisco.json' file.",
                ),
                fmt={"name": pkg_name},
            ),
        ) from exc
    with contextlib.suppress(KeyError):
        root_list.remove("LICENSE")
    with contextlib.suppress(KeyError):
        root_list.remove("README.md")
    with contextlib.suppress(KeyError):
        root_list.remove("requirements.txt")

    if root_list:
        raise RUValueError(
            format_str(
                _(
                    "'${{name}}' package contains files that not allowed in "
                    "the root directory.",
                ),
                fmt={"name": pkg_name},
            ),
        )


def get_extension_package_info(pkg_file: Path) -> ExtensionPackageInfo:
    """Get the extension package info.

    Args:
        pkg_file (Path): The package file.

    Returns:
        ExtensionPackageInfo: The extension package info.

    """
    json_opened = False
    try:
        with (
            zipfile.ZipFile(pkg_file, "r") as zip_file,
            zip_file.open("rubisco.json") as package_file,
        ):
            json_opened = True
            json_data = json5.loads(
                package_file.read().decode(DEFAULT_CHARSET),
            )
            pkg_config = AutoFormatDict(json_data)
            pkg_name = pkg_config.get("name", valtype=str)
            if not re.match(r"^[A-Za-z0-9_-.]+$", pkg_name):
                raise RUValueError(
                    format_str(
                        _(
                            "Package name '${{name}}' invalid.",
                        ),
                        fmt={"name": pkg_name},
                    ),
                    hint=_(
                        "Package name must be lowercase and only contain "
                        "0-9, a-z, A-Z, '_', '.' and '-'.",
                    ),
                )
            _pkg_check(zip_file, pkg_name)
            maintianers = pkg_config.get("maintainers", valtype=list)
            assert_iter_types(
                maintianers,
                str,
                RUValueError(_("Maintainers must be a list of strings.")),
            )
            iter_assert(
                maintianers,
                lambda x: "," not in x,
                RUValueError(_("Maintainers must not contain ','.")),
            )
            tags = pkg_config.get("tags", valtype=list)
            assert_iter_types(
                tags,
                str,
                RUValueError(_("Tags must be a list of strings.")),
            )

            def _check(x: str) -> bool:
                return re.match(r"^[a-z0-9_-]+$", x) is not None
            iter_assert(
                tags,
                _check,
                RUValueError(
                    _(
                        "Tags must be lowercase and only contain 0-9, a-z, A-Z"
                        ", '_' and '-'.",
                    ),
                ),
            )

            try:
                with zip_file.open("requirements.txt") as req_file:
                    requirements = req_file.read().decode(DEFAULT_CHARSET)
            except KeyError:
                requirements = None

            return ExtensionPackageInfo(
                pkg_name,
                Version(pkg_config.get("version", valtype=str)),
                pkg_config.get("description", valtype=str),
                pkg_config.get("homepage", valtype=str),
                maintianers,
                pkg_config.get("license", valtype=str),
                tags,
                requirements,
            )
    except zipfile.error as exc:
        raise RUValueError(
            format_str(
                _(
                    "[underline]'${{path}}'[/underline] is not a valid Rubisco"
                    " extension package. (Zip file)",
                ),
                fmt={"path": str(pkg_file)},
            ),
        ) from exc
    except json5.JSON5DecodeError as exc:
        raise RUValueError(
            format_str(
                _(
                    "[underline]'${{path}}'[/underline] package configuration "
                    "file is not a valid JSON5 file.",
                ),
                fmt={"path": str(pkg_file)},
            ),
        ) from exc
    except KeyError as exc:
        # If 'rubisco.json' file not found, ZipFile.open raises KeyError.
        if not json_opened:
            raise RUValueError(
                format_str(
                    _(
                        "[underline]'${{path}}'[/underline] Error when opening"
                        " 'rubisco.json': '${{msg}}'.",
                    ),
                    fmt={"path": str(pkg_file), "msg": exc.args[0]},
                ),
            ) from exc
        raise RUValueError(
            format_str(
                _(
                    "[underline]'${{path}}'[/underline] package configuration "
                    "file is missing a required key: '${{key}}'.",
                ),
                fmt={"path": str(pkg_file), "key": exc.args[0]},
            ),
        ) from exc


def install_extension(pkg_file: Path, dest: RUEnvironment) -> None:
    """Install the extension package.

    Args:
        pkg_file (Path): The package file.
        dest (RUEnvironment): The destination environment.

    """
    info = get_extension_package_info(pkg_file)
    call_ktrigger(
        IKernelTrigger.on_install_extension,
        dest=dest,
        ext_name=info.name,
        ext_version=info.version,
    )
    with TemporaryObject.new_directory() as temp_dir:
        extract_zip(pkg_file, temp_dir.path / "data")
        if (temp_dir.path / "data" / "requirements.txt").exists():
            install_requirements(
                dest,
                temp_dir.path / "data" / "requirements.txt",
            )
            shutil.move(
                (temp_dir.path / "data" / "requirements.txt"),
                dest.path / EXTENSIONS_DIR / info.name / "requirements.txt",
            )
        (temp_dir.path / "data" / info.name).rename(
            dest.path / EXTENSIONS_DIR / info.name,
        )
        if (temp_dir.path / "data" / "LICENSE").exists():
            (temp_dir.path / "data" / "LICENSE").rename(
                dest.path / EXTENSIONS_DIR / info.name / "LICENSE",
            )
        if (temp_dir.path / "data" / "README.md").exists():
            (temp_dir.path / "data" / "README.md").rename(
                dest.path / EXTENSIONS_DIR / info.name / "README.md",
            )

    call_ktrigger(
        IKernelTrigger.on_extension_installed,
        dest=dest.type,
        ext_name=info.name,
        ext_version=info.version,
    )


if __name__ == "__main__":
    pass
