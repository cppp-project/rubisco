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

import requests

from cppp_repoutils.constants import COPY_BUFSIZE, TIMEOUT
from cppp_repoutils.utils.fileutil import TemporaryObject
from cppp_repoutils.utils.log import logger
from cppp_repoutils.utils.nls import _
from cppp_repoutils.utils.output import ProgressBar

# TODO: Refactor.

__all__ = ["wget"]


def wget(url: str) -> TemporaryObject:
    """Download a file from the Internet.

    Args:
        url (str): The URL of the file.

    Returns:
        TemporaryObject: The downloaded file.
    """

    logger.debug("Downloading '%s' ...", url)

    with requests.head(url, timeout=TIMEOUT) as response:
        content_length = int(response.headers.get("Content-Length", 0))

        response.raise_for_status()
        file_obj = TemporaryObject.new_file()
        with open(file_obj.path, "wb") as file:
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

        return file_obj


if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    from cppp_repoutils.utils.yesno import yesno

    test_file = wget("https://ftp.gnu.org/pub/gnu/libiconv/libiconv-1.17.tar.gz")
    print("Downloaded", test_file)
    if yesno("Remove the downloaded file?", default=1, color="yellow"):
        test_file.remove()
        print("Removed", test_file)
    else:
        test_file.move()
