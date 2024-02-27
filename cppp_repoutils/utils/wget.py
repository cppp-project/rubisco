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

from cppp_repoutils.constants import COPY_BUFSIZE, TIMEOUT
from cppp_repoutils.utils.log import logger
from cppp_repoutils.utils.nls import _
from cppp_repoutils.utils.output import ProgressBar
from cppp_repoutils.utils.fileutil import assert_file_exists


__all__ = ["wget"]


def wget(url: str, save_to: Path, overwrite: bool = True) -> None:
    """Download a file from the Internet.

    Args:
        url (str): The URL of the file.
        save_to (Path): The path to save the file to.
        overwrite (bool): Whether to overwrite the file if it already exists.
    """

    if not overwrite:
        assert_file_exists(save_to)

    logger.debug("Downloading '%s' ...", url)

    with requests.head(url, timeout=TIMEOUT) as response:
        content_length = int(response.headers.get("Content-Length", 0))

        response.raise_for_status()
        with open(save_to, "wb") as file:
            with requests.get(url, stream=True, timeout=TIMEOUT) as response:
                response.raise_for_status()
                progress_bar = ProgressBar(
                    desc=_("Downloading '{underline}{url}{reset}' ..."),
                    desc_fmt={"url": url},
                    total=content_length,
                )
                for chunk in response.iter_content(chunk_size=COPY_BUFSIZE):
                    file.write(chunk)
                    file.flush()
                    progress_bar.update(len(chunk))
                progress_bar.close()
    logger.debug("Downloaded '%s' to '%s'.", url, save_to)


if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    URL = "https://ftp.gnu.org/pub/gnu/libiconv/libiconv-1.17.tar.gz"
    TARGET = Path("libiconv-1.17.tar.gz")

    wget(URL, TARGET)
