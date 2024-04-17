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
Git repository operations.
"""

import os
from pathlib import Path
from cppp_repoutils.utils.shell_command import run_command, popen_command
from cppp_repoutils.cli.output import output_step
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


def get_current_branch(path: Path) -> str:
    """
    Get the current branch of a git repository.

    Args:
        path: The path to the repository.

    Returns:
        The current branch of the repository.
    """

    command = [
        "git",
        "rev-parse",
        "--abbrev-ref",
        "HEAD",
    ]
    return popen_command(command, cwd=path, stderr=False)[0]


def update(path: Path, branch: str | None = None, shallow: bool = True) -> None:  # noqa: E501
    """
    Update a git repository.

    Args:
        path: The path to the repository.
        branch: The branch to clone. Default is None.
        shallow: Whether to perform a shallow clone. Default is True.
    """

    path = path.absolute()

    output_step(
        _(
            "Updating '{underline}{path}{reset}' ..."  # noqa: E501
        ),
        fmt={"path": str(path)},
    )

    if not path.exists():
        logger.warning("'%s' does not exist, Ignored.", path)
        output_step(
            _("{underline}{path}{reset} does not exist, Ignored."),
            fmt={"path": str(path)},
        )
        return

    # Update repository.
    command = [
        "git",
        "pull",
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
    run_command(command, strict=True, cwd=path)


if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    clone("https://github.com/Crequency/KitX.git", Path("KitX"))
    update(Path("KitX"))
    print("Current branch: ", get_current_branch(Path("KitX")))
