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

"""Download a file from the Internet."""

from __future__ import annotations

from typing import TYPE_CHECKING

import requests

from rubisco.config import COPY_BUFSIZE, TIMEOUT
from rubisco.lib.fileutil import check_file_exists
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

if TYPE_CHECKING:
    from pathlib import Path

__all__ = ["wget"]


def wget(
    url: str,
    save_to: Path,
    *,
    overwrite: bool = True,
) -> None:
    """Download a file from the Internet.

    Args:
        url (str): The URL of the file.
        save_to (Path): The path to save the file to.
        overwrite (bool): Whether to overwrite the file if it already exists.

    """
    if not overwrite:
        check_file_exists(save_to)

    logger.debug("Downloading '%s' ...", url)

    content_length = 0
    with requests.head(url, timeout=TIMEOUT) as response:
        response.raise_for_status()
        content_length = int(response.headers.get("Content-Length", 0))

    with (
        save_to.open("wb") as file,
        requests.get(url, stream=True, timeout=TIMEOUT) as response,
    ):
        response.raise_for_status()
        task_msg = fast_format_str(
            _("Downloading ${{url}} ..."),
            fmt={"url": url},
        )
        task_name = _("Download")
        call_ktrigger(
            IKernelTrigger.on_new_task,
            task_start_msg=task_msg,
            task_name=task_name,
            total=float(content_length),
        )
        for chunk in response.iter_content(chunk_size=COPY_BUFSIZE):
            file.write(chunk)
            file.flush()
            call_ktrigger(
                IKernelTrigger.on_progress,
                task_name=task_name,
                current=float(len(chunk)),
                delta=True,
            )
        call_ktrigger(IKernelTrigger.on_finish_task, task_name=task_name)
    logger.debug("Downloaded '%s' to '%s'.", url, save_to)
