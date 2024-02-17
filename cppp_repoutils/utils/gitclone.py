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

from threading import Lock
from typing import Union
import git.cmd
from git.repo import Repo
from git.remote import RemoteProgress
from cppp_repoutils.utils.output import output_step, ProgressBar
from cppp_repoutils.utils.nls import _
from cppp_repoutils.utils.log import logger

__all__ = ["clone"]

git.cmd.log = logger


class _ProgressPrinter(RemoteProgress):

    __progress_bar: ProgressBar = None
    __lock: Lock = Lock()

    def line_dropped(self, line: str) -> None:
        pass

    def update(
        self,
        op_code: int,
        cur_count: Union[str, float],
        max_count: Union[str, float, None] = None,
        message: str = "",
    ) -> None:
        with self.__lock:
            if not isinstance(cur_count, float | int) or not isinstance(
                max_count, float | int
            ):
                return
            if op_code & RemoteProgress.BEGIN:
                if op_code & RemoteProgress.CHECKING_OUT:
                    self.__progress_bar = ProgressBar(
                        desc=_("Checking out files ..."),
                        total=max_count,
                    )
                elif op_code & RemoteProgress.COMPRESSING:
                    self.__progress_bar = ProgressBar(
                        desc=_("Compressing objects ..."),
                        total=max_count,
                    )
                elif op_code & RemoteProgress.COUNTING:
                    self.__progress_bar = ProgressBar(
                        desc=_("Counting objects ..."),
                        total=max_count,
                    )
                elif op_code & RemoteProgress.FINDING_SOURCES:
                    self.__progress_bar = ProgressBar(
                        desc=_("Finding sources ..."),
                        total=max_count,
                    )
                elif op_code & RemoteProgress.RECEIVING:
                    self.__progress_bar = ProgressBar(
                        desc=_("Receiving objects ..."),
                        total=max_count,
                    )
                elif op_code & RemoteProgress.RESOLVING:
                    self.__progress_bar = ProgressBar(
                        desc=_("Resolving deltas ..."),
                        total=max_count,
                    )
                elif op_code & RemoteProgress.WRITING:
                    self.__progress_bar = ProgressBar(
                        desc=_("Writing objects ..."),
                        total=max_count,
                    )
            elif op_code & RemoteProgress.END:
                # self.__progress_bar.update(max_count)
                self.__progress_bar.close()
            else:
                self.__progress_bar.set_progress(cur_count)


def clone(url, path, branch="main", depth=None) -> Repo:
    """
    Clone a git repository.

    Args:
        url: The URL of the git repository.
        path: The path to clone the repository to.
        branch: The branch to clone.
        depth: The depth to clone.

    Returns:
        The git repository object.
    """

    output_step(
        _(
            "Cloning '{underline}{url}{reset}' into '{underline}{path}{reset}' ..."  # noqa: E501
        ),
        fmt={"url": url, "path": path},
    )

    repo = Repo.clone_from(
        url,
        path,
        progress=_ProgressPrinter(),
        branch=branch,
        depth=depth,
        allow_unsafe_protocols=True,
        allow_unsafe_options=True,
    )
    return repo


if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    clone(
        "https://git.savannah.gnu.org/git/libiconv.git",
        "libiconv",
        branch="master",
        depth=None,
    )
