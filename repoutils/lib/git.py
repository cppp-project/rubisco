# -*- coding: utf-8 -*-
# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2024 The C++ Plus Project.
# This file is part of the repoutils.
#
# repoutils is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# repoutils is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Mirrorlist for extention installer.
"""

from pathlib import Path

from repoutils.lib.l10n import _
from repoutils.lib.log import logger
from repoutils.lib.process import Process, popen
from repoutils.lib.variable import format_str
from repoutils.shared.ktrigger import IKernelTrigger, call_ktrigger


def is_git_repo(path: Path) -> bool:
    """Check if a directory is a git repository.

    Args:
        path (Path): Path to the directory.

    Returns:
        bool: True if the directory is a git repository.
    """

    _stdout, _stderr, retcode = popen(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=path,
        stderr=False,
        stdout=False,
        strict=False,
    )
    return retcode == 0


def git_update(path: Path, branch: str = "main"):
    """Update a git repository.

    Args:
        path (Path): Path to the repository.
        branch (str, optional): Branch to update. Defaults to "main".
    """

    if not path.exists():
        logger.error("Repository '%s' does not exist.", str(path))
        raise FileNotFoundError(
            format_str(
                _("Repository '{underline}{path}{reset}' does not exist."),
                fmt={"path": str(path)},
            )
        )

    logger.info("Updating repository '%s'...", str(path))
    call_ktrigger(IKernelTrigger.on_update_git_repo, path=path, branch=branch)
    Process(["git", "pull", "--verbose"], cwd=path).run()
    logger.info("Repository '%s' updated.", str(path))


def git_clone(
    url: str,
    path: Path,
    branch: str = "main",
    shallow: bool = True,
    strict: bool = False,
):
    """Clone a git repository.

    Args:
        url (str): Repository URL.
        path (Path): Path to clone the repository.
        branch (str, optional): Branch to clone. Defaults to "main".
        shallow (bool, optional): Shallow clone. Defaults to True.
        strict (bool, optional): Raise an error if the repository already
            exists. If False, the repository will be updated. Defaults to
            False.
    """

    if is_git_repo(path):
        if strict:
            logger.error("Repository already exists.")
            raise FileExistsError(
                format_str(
                    _("Repository '{underline}{path}{reset}' already exists."),
                    fmt={"path": str(path)},
                )
            )
        logger.warning("Repository already exists, Updating...")
        git_update(path, branch)
        return

    logger.info("Cloning repository '%s' to '%s'...", url, str(path))
    call_ktrigger(
        IKernelTrigger.on_clone_git_repo,
        url=url,
        path=path,
        branch=branch,
    )
    cmd = ["git", "clone", "--verbose", "--branch", branch, url, str(path)]
    if shallow:
        cmd.append("--depth")
        cmd.append("1")
    Process(cmd).run()
    logger.info("Repository '%s' cloned.", str(path))


def git_get_remote(path: Path, remote: str = "origin") -> str:
    """Get the URL of a remote repository.

    Args:
        path (Path): Path to the repository.
        remote (str, optional): Remote name. Defaults to "origin".

    Returns:
        str: Remote URL.
    """

    return popen(["git", "remote", "get-url", remote], cwd=path, stderr=False)[
        0
    ]  # noqa: E501


def git_set_remote(path: Path, remote: str, url: str):
    """Set the URL of a remote repository.

    Args:
        path (Path): Path to the repository.
        remote (str): Remote name.
        url (str): Remote URL.
    """

    popen(["git", "remote", "set-url", remote, url], cwd=path)


if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    import shutil

    from repoutils.lib.fileutil import TemporaryObject
    from repoutils.shared.ktrigger import bind_ktrigger_interface

    class _TestKTrigger(IKernelTrigger):
        def pre_exec_process(self, proc: Process) -> None:
            print(f"=> Executing: {proc.cmd} ...")

        def on_update_git_repo(
            self,
            path: Path,
            branch: str,
        ) -> None:
            print(f"=> Updating Git repository '{path}'({branch}) ...")

        def on_clone_git_repo(
            self,
            url: str,
            path: Path,
            branch: str,
        ) -> None:
            print(
                f"=> Cloing Git repository '{url}' into '{path}'({branch}) ..."
            )  # noqa: E501

    bind_ktrigger_interface("test", _TestKTrigger())

    # Test: Is a Git repository.
    git_repo = TemporaryObject.new_directory()
    non_git_repo = TemporaryObject.new_directory()
    Process(["git", "init"], cwd=git_repo.path).run()
    assert is_git_repo(git_repo.path) is True
    assert is_git_repo(non_git_repo.path) is False

    # Test: Clone a repository shallowly.
    git_clone(
        "https://git.savannah.gnu.org/git/autoconf.git",
        Path("autoconf"),
        branch="master",
        shallow=True,
    )

    # Test: Clone a existing repository without strict mode.
    git_clone(
        "https://git.savannah.gnu.org/git/autoconf.git",
        Path("autoconf"),
        branch="master",
        shallow=True,
        strict=False,
    )

    # Test: Clone a existing repository with strict mode.
    try:
        git_clone(
            "https://git.savannah.gnu.org/git/autoconf.git",
            Path("autoconf"),
            branch="master",
            shallow=True,
            strict=True,
        )
        assert False, "Should raise a FileExistsError."
    except FileExistsError:
        pass

    # Test: Update a repository.
    git_update(Path("autoconf"), branch="master")

    # Test: Update a non-existing repository.
    try:
        git_update(Path("autoconf2"), branch="master")
        assert False, "Should raise a FileNotFoundError."
    except FileNotFoundError:
        pass

    shutil.rmtree("autoconf")
    print("=> Done.")
