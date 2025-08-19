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

"""Rubisco changelog generator."""

import datetime
from dataclasses import dataclass
from pathlib import Path

from pygit2 import (  # pylint: disable=E0611
    GIT_SORT_TIME,
    Commit,
    GitError,
    Repository,
)
from rubisco.config import DEFAULT_CHARSET
from rubisco.shared.api.exception import RUError, RUValueError
from rubisco.shared.api.kernel import load_project_config
from rubisco.shared.api.l10n import _
from rubisco.shared.api.variable import (
    AutoFormatDict,
    VariableContainer,
    fast_format_str,
    format_str,
    make_pretty,
)
from rubisco.shared.api.uci import ProgressTask
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

from changelog.config import CHANGELOG_FORMAT, TIME_FORMAT
from changelog.logger import logger

__all__ = ["gen_project_changelog"]


@dataclass
class ChangeLogNode:  # pylint: disable=R0902
    """A node in the changelog linked list."""

    config: AutoFormatDict
    commit_id: str
    message: str
    added_lines: int
    removed_lines: int
    changed_files: int
    timestamp: int
    time_offset: int
    author: str
    email: str
    next: "ChangeLogNode | None" = None

    def get_time_str(self) -> str:
        """Get the time string of the commit."""
        time_format = self.config.get(
            "changelog-time-format",
            TIME_FORMAT,
            valtype=str,
        )

        datetime_str = datetime.datetime.fromtimestamp(
            self.timestamp,
            tz=datetime.UTC,
        ).strftime(time_format)
        return f"{datetime_str}"

    def __str__(self) -> str:
        """Generate a string representation of the changelog node.

        Returns:
            str: Formatted string with commit details.

        """
        time_str = self.get_time_str()
        offset_str = f"{self.time_offset:+d}"
        with VariableContainer(
            fmt={
                "time": time_str,
                "time-offset": offset_str,
                "author": self.author,
                "email": self.email,
                "message": self.message,
                "changed-files": self.changed_files,
                "added-lines": self.added_lines,
                "removed-lines": self.removed_lines,
            },
        ):
            return self.config.get(
                "changelog-format",
                format_str(CHANGELOG_FORMAT),
                valtype=str,
            )


def _gen_changelog_from_commit(
    commit: Commit,
    prev_commit: Commit | None,
    config: AutoFormatDict,
) -> ChangeLogNode:
    prev_tree = prev_commit.tree if prev_commit and prev_commit.tree else None
    diff = (
        commit.tree.diff_to_tree(swap=True)
        if not prev_tree
        else prev_tree.diff_to_tree(commit.tree)
    )
    added_lines = 0
    removed_lines = 0
    changed_files = len(diff)
    for patch in diff:
        for hunk in patch.hunks:
            for line in hunk.lines:
                if line.origin == "+":
                    added_lines += 1
                elif line.origin == "-":
                    removed_lines += 1

    return ChangeLogNode(
        config=config,
        commit_id=str(commit.id),
        message=commit.message.strip(),
        added_lines=added_lines,
        removed_lines=removed_lines,
        changed_files=changed_files,
        timestamp=commit.commit_time,
        time_offset=commit.commit_time_offset,
        author=commit.author.name,
        email=commit.author.email,
        next=None,
    )


def gen_changelog(
    repo: Repository,
    config: AutoFormatDict,
) -> ChangeLogNode | None:
    """Generate a changelog from the repository.

    Args:
        repo (Repository): The pygit2 repository object.
        config (AutoFormatDict): Project configuration for formatting.

    Returns:
        ChangeLogNode: The head of the changelog linked list.

    Raises:
        NoCommitsError: If no commits are found in the repository.

    """
    current_branch_name = repo.head.shorthand
    current_branch = repo.lookup_branch(current_branch_name)

    head_node = None
    current_node = None
    prev_commit = None

    with ProgressTask(
        title=_("Generating changelog"),
        msg=fast_format_str(
            _("Generating changelog for ${{repo}} ..."),
            fmt={"repo": make_pretty(repo_path)},
        ),
        total=current_branch.target.count(),
    )
    for commit in repo.walk(
        current_branch.target,
        GIT_SORT_TIME,  # type: ignore[reportArgumentType]
    ):
        new_node = _gen_changelog_from_commit(commit, prev_commit, config)

        if head_node is None:
            head_node = new_node
            current_node = new_node
        else:
            if not current_node:
                msg = "This should never happen."
                raise AssertionError(msg)
            current_node.next = new_node
            current_node = new_node

        prev_commit = commit

    return head_node


def gen_repo_changelog(
    repo_path: Path,
    config: AutoFormatDict,
) -> str:
    """Generate a changelog from the repository path.

    Args:
        repo_path (Path): The path to the repository.
        config (AutoFormatDict): Project configuration for formatting.

    Returns:
        str: The formatted changelog as a string.

    """
    res = ""
    try:
        repo = Repository(str(repo_path.resolve()))
        head_node = gen_changelog(repo, config)
        current_node = head_node
        while current_node:
            res += str(current_node) + "\n\n"
            current_node = current_node.next
        return res.strip() + "\n"
    except GitError as e:
        msg = fast_format_str(
            _("Failed to generate changelog: ${{exc}}"),
            fmt={"exc": str(e)},
        )
        raise RUValueError(msg) from e


def gen_project_changelog(
    repo_path: Path,
    output_path: Path,
) -> None:
    """Generate a changelog for the Rubisco project at the given path.

    Args:
        repo_path (Path): The path to the repository.
        output_path (Path): The path to save the generated changelog.

    """
    try:
        config = load_project_config(repo_path).config
    except (RUError, OSError) as e:
        logger.warning(
            "Not a valid Rubisco project: %s: %s",
            repo_path,
            e,
            exc_info=True,
        )
        config = None
        call_ktrigger(
            IKernelTrigger.on_warning,
            message=fast_format_str(
                _(
                    "Directory ${{repo}} is not a valid Rubisco project, "
                    "treat as a regular Git repository: ${{exc}}",
                ),
                fmt={"repo": make_pretty(repo_path), "exc": str(e)},
            ),
        )
    if config is None:
        config = AutoFormatDict()

    data = gen_repo_changelog(repo_path, config)

    with output_path.open("w", encoding=DEFAULT_CHARSET) as f:
        f.write(data)
