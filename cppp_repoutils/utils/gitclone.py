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
Clone a git repository.
"""

import os
from pathlib import Path
from cppp_repoutils.utils.shell_command import run_command
from cppp_repoutils.utils.output import output_step
from cppp_repoutils.utils.nls import _
from cppp_repoutils.utils.log import logger


def clone(
    url: str, path: Path, branch: str | None = None, shallow: bool = True
) -> None:
    """
    Clone a git repository.

    Args:
        url: The URL of the git repository.
        path: The path to clone the repository to.
        branch: The branch to clone. Default is None.
        shallow: Whether to perform a shallow clone. Default is True.
    """

    path = path.absolute()

    output_step(
        _(
            "Cloning '{underline}{url}{reset}' to '{underline}{path}{reset}' ..."  # noqa: E501
        ),
        fmt={"url": url, "path": str(path)},
    )

    if path.exists():
        logger.warning("'%s' already exists, Ignored.", path)
        output_step(
            _("{underline}{path}{reset} already exists, Ignored."),
            fmt={"path": str(path)},
        )
        return

    # Clone repository.
    command = [
        "git",
        "clone",
        str(url),
        str(path.absolute()),
    ]
    command.extend(
        [
            "--progress",
            "--verbose",
            "--recurse-submodules",
            "--remote-submodules",
            "--jobs",
            str(os.cpu_count()),
        ]
    )

    if branch is not None:
        command.extend(["--branch", str(branch)])
    if shallow:
        command.extend(["--depth", "1", "--shallow-submodules"])
    os.makedirs(path.parent, exist_ok=True)
    run_command(command, strict=True, cwd=path.parent)

    # Clone submodules.


if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    clone("https://github.com/Crequency/KitX.git", Path("KitX"))
