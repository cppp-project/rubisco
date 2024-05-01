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
Download a file from the Internet.
"""

from pathlib import Path

import requests

from repoutils.config import COPY_BUFSIZE, TIMEOUT
from repoutils.lib.fileutil import check_file_exists
from repoutils.lib.l10n import _
from repoutils.lib.log import logger
from repoutils.lib.variable import format_str
from repoutils.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = ["wget"]


def wget(url: str, save_to: Path, overwrite: bool = True) -> None:
    """Download a file from the Internet.

    Args:
        url (str): The URL of the file.
        save_to (Path): The path to save the file to.
        overwrite (bool): Whether to overwrite the file if it already exists.
    """

    if not overwrite:
        check_file_exists(save_to)

    logger.debug("Downloading '%s' ...", url)

    with requests.head(url, timeout=TIMEOUT) as response:
        content_length = int(response.headers.get("Content-Length", 0))

        response.raise_for_status()
        with open(save_to, "wb") as file:
            with requests.get(url, stream=True, timeout=TIMEOUT) as response:
                response.raise_for_status()
                task_name = format_str(
                    _(
                        "Downloading '{bold}{underline}{url}{reset}' ...",
                    ),
                    fmt={"url": url},
                )
                call_ktrigger(
                    IKernelTrigger.on_new_task,
                    task_name=task_name,
                    task_type=IKernelTrigger.TASK_DOWNLOAD,
                    total=content_length,
                )
                for chunk in response.iter_content(chunk_size=COPY_BUFSIZE):
                    file.write(chunk)
                    file.flush()
                    call_ktrigger(
                        IKernelTrigger.on_progress,
                        task_name=task_name,
                        current=len(chunk),
                        delta=True,
                    )
                call_ktrigger(
                    IKernelTrigger.on_finish_task,
                    task_name=task_name,
                )
    logger.debug("Downloaded '%s' to '%s'.", url, save_to)


if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    print("Make sure you have Internet connection. Otherwise, it will fail.")

    from repoutils.lib.fileutil import rm_recursive
    from repoutils.shared.ktrigger import bind_ktrigger_interface

    URL = "https://musl.libc.org/releases/musl-1.2.5.tar.gz"
    TARGET = Path("musl-1.2.5.tar.gz")

    class _TestKTrigger(IKernelTrigger):
        _prog_total: int | float
        _prog_current: int | float

        def on_new_task(
            self, task_name: str, task_type: int, total: int | float
        ) -> None:
            print("on_new_task():", task_name, task_type, total)
            self._prog_total = total
            self._prog_current = 0

        def on_progress(
            self,
            task_name: str,
            current: int | float,
            delta: bool = False,
        ):
            if delta:
                self._prog_current += current
            else:
                self._prog_current = current
            print(
                "on_progress():",
                task_name,
                self._prog_current,
                "/",
                self._prog_total,
                end="\r",
            )

        def on_finish_task(self, task_name: str):
            print("\non_finish_task():", task_name)

    kt = _TestKTrigger()
    bind_ktrigger_interface("test", kt)

    wget(URL, TARGET)
    rm_recursive(TARGET)
