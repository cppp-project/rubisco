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

import os
from typing import TYPE_CHECKING

from rubisco.config import PIP_LOG_FILE
from rubisco.kernel.mirrorlist import get_url
from rubisco.lib.l10n import _
from rubisco.lib.process import Process
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

if TYPE_CHECKING:
    from rubisco.envutils.env import RUEnvironment
    from rubisco.lib.pathlib import Path

__all__ = ["install_pip_package", "install_requirements"]


def _exec_pip(dest: RUEnvironment, args: list[str]) -> None:
    pip_path = dest.path / "bin" / "pip"
    if os.name == "nt":
        pip_path = dest.path / "Scripts" / "pip.exe"
    if not pip_path.exists():
        msg = f"Pip not found: '{pip_path}'"
        raise ValueError(msg)  # Internal error. Should not happen.

    Process(
        [
            str(pip_path.absolute()),
            "--disable-pip-version-check",
            "--require-virtualenv",
            "--verbose",
            "--no-color",
            "--log",
            str(PIP_LOG_FILE),
            *args,
        ],
    ).run()


def install_pip_package(dest: RUEnvironment, pkgs: list[str]) -> None:
    """Install Pip packages to the specified environment.

    Args:
        dest (RUEnvironment): Destination environment.
        pkgs (list[str]): Pip packages.

    """
    if not pkgs:
        return

    if dest.is_global():
        call_ktrigger(
            IKernelTrigger.on_hint,
            message=_(
                "You are installing a extension to the global environment. "
                "Please make sure that you have the right permissions.",
            ),
        )

    with dest:
        index_url = get_url("/@pypi")
        _exec_pip(dest, ["install", *pkgs, "--index-url", index_url])


def install_requirements(dest: RUEnvironment, req_file: Path) -> None:
    """Install Pip packages from the requirements file.

    Args:
        dest (RUEnvironment): Destination environment.
        req_file (Path): Requirements file.

    """
    req_file = req_file.absolute()
    # Poor readability but works.
    install_pip_package(dest, ["-r", str(req_file)])
