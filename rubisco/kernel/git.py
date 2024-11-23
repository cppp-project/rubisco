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

"""Mirrorlist for extension installer."""

from rubisco.kernel.mirrorlist import get_url
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.pathlib import Path
from rubisco.lib.process import Process
from rubisco.lib.variable import format_str, make_pretty
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = [
    "git_clone",
    "git_get_remote",
    "git_has_remote",
    "git_set_remote",
    "git_update",
    "is_git_repo",
]


def is_git_repo(path: Path) -> bool:
    """Check if a directory is a git repository.

    Args:
        path (Path): Path to the directory.

    Returns:
        bool: True if the directory is a git repository.

    """
    if not path.exists():
        return False

    _stdout, _stderr, retcode = Process(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=path,
    ).popen(
        stdout=True,
        stderr=1,
        fail_on_error=False,
    )
    return retcode == 0


def git_update(path: Path, branch: str = "main") -> None:
    """Update a git repository.

    Args:
        path (Path): Path to the repository.
        branch (str, optional): Branch to update. Defaults to "main".

    """
    if not path.exists():
        logger.error("Repository '%s' does not exist.", str(path))
        raise FileNotFoundError(
            format_str(
                _(
                    "Repository '[underline]${{path}}[/underline]' not found.",
                ),
                fmt={"path": make_pretty(path.absolute())},
            ),
        )

    logger.info("Updating repository '%s'...", str(path))
    call_ktrigger(IKernelTrigger.on_update_git_repo, path=path, branch=branch)
    Process(["git", "pull", "--verbose"], cwd=path).run()
    logger.info("Repository '%s' updated.", str(path))


def git_clone(  # pylint: disable=R0913, R0917 # noqa: PLR0913
    url: str,
    path: Path,
    branch: str = "main",
    shallow: bool = True,  # noqa: FBT001 FBT002
    strict: bool = False,  # noqa: FBT001 FBT002
    use_fastest: bool = True,  # noqa: FBT001 FBT002
) -> None:
    """Clone a git repository.

    Args:
        url (str): Repository URL.
        path (Path): Path to clone the repository.
        branch (str, optional): Branch to clone. Defaults to "main".
        shallow (bool, optional): Shallow clone. Defaults to True.
        strict (bool, optional): Raise an error if the repository already
            exists. If False, the repository will be updated. Defaults to
            False.
        use_fastest (bool, optional): Use the fastest mirror. Defaults to True.

    """
    if is_git_repo(path):
        if strict:
            logger.error("Repository already exists.")
            raise FileExistsError(
                format_str(
                    _(
                        "Repository '[underline]${{path}}[/underline]' already"
                        " exists.",
                    ),
                    fmt={"path": str(path)},
                ),
            )
        logger.warning("Repository already exists, Updating...")
        git_update(path, branch)
        return

    old_url = url
    url = get_url(url, use_fastest=use_fastest)

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

    if old_url != url:  # Reset the origin URL to official.
        git_set_remote(path, "origin", get_url(old_url, use_fastest=False))
        git_set_remote(path, "mirror", url)
        git_branch_set_upstream(path, branch, "origin")


def git_has_remote(path: Path, remote: str) -> bool:
    """Check if a remote repository exists.

    Args:
        path (Path): Path to the repository.
        remote (str, optional): Remote name.

    Returns:
        bool: True if the remote repository exists.

    """
    _stdout, _stderr, retcode = Process(
        ["git", "remote", "get-url", remote],
        cwd=path,
    ).popen(
        stdout=False,
        stderr=0,
        fail_on_error=False,
    )
    return retcode == 0


def git_get_remote(path: Path, remote: str = "origin") -> str:
    """Get the URL of a remote repository.

    Args:
        path (Path): Path to the repository.
        remote (str, optional): Remote name. Defaults to "origin".

    Returns:
        str: Remote URL.

    """
    return Process(["git", "remote", "get-url", remote], cwd=path).popen(
        stderr=False,
    )[0]


def git_set_remote(path: Path, remote: str, url: str) -> None:
    """Set the URL of a remote repository.

    Args:
        path (Path): Path to the repository.
        remote (str): Remote name.
        url (str): Remote URL.

    """
    if git_has_remote(path, remote):
        Process(["git", "remote", "set-url", remote, url], cwd=path).run()
        return
    Process(["git", "remote", "add", remote, url], cwd=path).run()


def git_branch_set_upstream(
    path: Path,
    branch: str,
    remote: str = "origin",
) -> None:
    """Set the upstream of a branch.

    Args:
        path (Path): Path to the repository.
        branch (str): Branch name.
        remote (str, optional): Remote name. Defaults to "origin".

    """
    Process(
        ["git", "branch", "--set-upstream-to", f"{remote}/{branch}", branch],
        cwd=path,
    ).run()


if __name__ == "__main__":
    import shutil
    import sys

    import colorama
    import rich

    from rubisco.lib.fileutil import (  # pylint: disable=ungrouped-imports
        TemporaryObject,
    )
    from rubisco.shared.ktrigger import bind_ktrigger_interface

    colorama.init()

    class _GitTestKTrigger(IKernelTrigger):
        def on_update_git_repo(
            self,
            path: Path,
            branch: str,
        ) -> None:
            rich.print(
                "[blue]=>[/blue] Updating Git repository "
                f"'[underline]{path}[/underline]'({branch}) ...",
            )

        def on_clone_git_repo(
            self,
            url: str,
            path: Path,
            branch: str,
        ) -> None:
            rich.print(
                f"[blue]=>[/blue] Cloing Git repository "
                f"{url} into "
                f"'[underline]{path}[/underline]'({branch}) ...",
            )

        def pre_speedtest(self, host: str) -> None:
            rich.print(
                f"[blue]=>[/blue] Testing speed for {host} ...",
                end="\n",
            )

        def post_speedtest(self, host: str, speed: int) -> None:
            speed_str = f"{speed} us" if speed != -1 else " - CANCELED"
            rich.print(f"[blue]::[/blue] Speed: {host} {speed_str}", end="\n")

        def pre_exec_process(self, proc: Process) -> None:
            rich.print(
                f"[blue]=>[/blue] Executing: [cyan]{proc.origin_cmd}[/cyan]",
            )
            sys.stdout.write(colorama.Fore.LIGHTBLACK_EX)
            sys.stdout.flush()

        def post_exec_process(
            self,
            proc: Process,  # noqa: ARG002
            retcode: int,
            raise_exc: bool,  # noqa: ARG002 FBT001
        ) -> None:
            sys.stdout.write(colorama.Fore.RESET)
            sys.stdout.flush()
            if retcode != 0:
                rich.print(f"[red] Process failed with code {retcode}.[/red]")

    bind_ktrigger_interface("test", _GitTestKTrigger())

    # Test: Is a Git repository.
    git_repo = TemporaryObject.new_directory()
    non_git_repo = TemporaryObject.new_directory()
    Process(["git", "init"], cwd=git_repo.path).run()
    assert is_git_repo(git_repo.path) is True  # noqa: S101
    assert is_git_repo(non_git_repo.path) is False  # noqa: S101

    # Test: Clone a repository shallowly.
    git_clone(
        "cppp-project/cppp-reiconv@github",
        Path("cppp-reiconv"),
        branch="main",
        shallow=True,
    )

    # Test: Clone a existing repository without strict mode.
    git_clone(
        "/hello@savannah",
        Path("hello"),
        branch="master",
        shallow=True,
        strict=False,
    )

    # Test: Clone a existing repository with strict mode.
    try:
        git_clone(
            "/hello@savannah",
            Path("hello"),
            branch="master",
            shallow=True,
            strict=True,
        )
        _MSG = "Should raise a FileExistsError."
        raise AssertionError(_MSG)
    except FileExistsError:
        pass

    # Test: Update a repository.
    git_update(Path("hello"), branch="master")

    # Test: Update a non-existing repository.
    try:
        git_update(Path("libiconv"), branch="master")
        _MSG = "Should raise a FileNotFoundError."
        raise AssertionError(_MSG)
    except FileNotFoundError:
        pass

    shutil.rmtree("hello")
    shutil.rmtree("cppp-reiconv")
    rich.print("[blue]=>[/blue] Done.")
