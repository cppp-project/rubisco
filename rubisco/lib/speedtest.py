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

"""Test the speed of the given host."""

import time

import aiohttp
import aiohttp.client_exceptions

from rubisco.config import TIMEOUT
from rubisco.lib.log import logger

__all__ = ["C_INTMAX", "url_speedtest"]

C_INTMAX = 0xFFFFFFFF


async def url_speedtest(url: str) -> int:
    """Test the speed of the given url.

    Args:
        url (str): URL to test.

    Returns:
        int: Speed of the given URL. (us)

    """
    logger.debug("Testing speed for '%s' ...", url)
    start = time.time_ns()

    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(TIMEOUT),
        raise_for_status=False,
        trust_env=True,
        read_bufsize=1,  # We don't need to read the response.
    ) as session:
        try:
            async with session.get(url) as response:
                response.close()
        except aiohttp.client_exceptions.ClientResponseError:
            pass  # Response means reachable.
        except aiohttp.client_exceptions.ClientError:
            logger.warning("Failed to test speed of '%s'.", url, exc_info=True)
            return C_INTMAX
        delta = (time.time_ns() - start) // 1000
        logger.info("Testing speed for '%s' ... %dus", url, delta)
        return delta


if __name__ == "__main__":
    import asyncio

    import rich

    # Test: Test the speed of the given URL.
    speed = asyncio.run(url_speedtest("https://www.gnu.org"))
    rich.print(f"Speed of https://www.gnu.org : {speed} us.")
