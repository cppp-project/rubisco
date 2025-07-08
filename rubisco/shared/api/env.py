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

"""Rubisco extension API for `rubisco.envutils`."""

from rubisco.envutils.env import (
    GLOBAL_ENV,
    USER_ENV,
    WORKSPACE_ENV,
    RUEnvironment,
)
from rubisco.envutils.env_db import RUEnvDB
from rubisco.envutils.env_type import EnvType
from rubisco.envutils.packages import (
    ExtensionPackageInfo,
    get_extension_package_info,
    install_extension,
    query_packages,
    uninstall_extension,
    upgrade_extension,
)
from rubisco.envutils.pip import install_pip_package, install_requirements
from rubisco.envutils.utils import add_venv_to_syspath, is_venv

__all__ = [
    "GLOBAL_ENV",
    "USER_ENV",
    "WORKSPACE_ENV",
    "EnvType",
    "ExtensionPackageInfo",
    "RUEnvDB",
    "RUEnvironment",
    "add_venv_to_syspath",
    "get_extension_package_info",
    "install_extension",
    "install_pip_package",
    "install_requirements",
    "is_venv",
    "query_packages",
    "uninstall_extension",
    "upgrade_extension",
]
