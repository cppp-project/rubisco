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
Git URL parser that supports mirrorlist.
e.g:
    "https://github.com/{user}/{repo}.git"
"""

import asyncio
import re

import json5 as json
from urllib3.util import parse_url

from repoutils.config import (DEFAULT_CHARSET, GLOBAL_CONFIG_DIR,
                              USER_CONFIG_DIR, WORKSPACE_CONFIG_DIR)
from repoutils.lib.log import logger
from repoutils.lib.speedtest import C_INTMAX, url_speedtest
from repoutils.lib.variable import AutoFormatDict, format_str
from repoutils.shared.ktrigger import IKernelTrigger, call_ktrigger

WORKSPACE_MIRRORLIST_FILE = WORKSPACE_CONFIG_DIR / "mirrorlist.json"
USER_MIRRORLIST_FILE = USER_CONFIG_DIR / "mirrorlist.json"
GLOBAL_MIRRORLIST_FILE = GLOBAL_CONFIG_DIR / "mirrorlist.json"

mirrorlist: AutoFormatDict = AutoFormatDict()

for mirrorlist_file in [
    GLOBAL_MIRRORLIST_FILE,
    USER_MIRRORLIST_FILE,
    WORKSPACE_MIRRORLIST_FILE,
]:
    if mirrorlist_file.exists():
        try:
            with mirrorlist_file.open("r", encoding=DEFAULT_CHARSET) as f:
                mirrorlist.merge(json.load(f))
        except (OSError, json.JSON5DecodeError) as exc:
            logger.warning(
                "Failed to load mirrorlist file: %s: %s", mirrorlist_file, exc
            )


async def _speedtest(future: asyncio.Future, mirror: str, url: str):
    try:
        parsed_url = parse_url(url)
        url = f"{parsed_url.scheme}://{parsed_url.host}"  # Host only.
        call_ktrigger(IKernelTrigger.pre_speedtest, host=url)
        speed = await url_speedtest(url)
        if future.done():
            return
        call_ktrigger(IKernelTrigger.post_speedtest, host=url, speed=speed)
        future.set_result(mirror)
    except asyncio.exceptions.CancelledError:
        call_ktrigger(IKernelTrigger.post_speedtest, host=url, speed=-1)


async def find_fastest_mirror(
    host: str,
    protocol: str = "http",
) -> tuple[str, str]:
    """Find the fastest mirror in mirrorlist.

    Args:
        host (str): The host you want to find.
        protocol (str): Connection protocol. Defaults to "http".
            We only support HTTP(s) for now.

    Returns:
        tuple[str, str]: The mirror host name and its url.
    """

    try:
        mlist: AutoFormatDict
        mlist = mirrorlist.get(host, valtype=dict).get(protocol, valtype=dict)
        future = asyncio.get_event_loop().create_future()
        tasks: list[asyncio.Task] = []
        for mirror, murl in mlist.items():
            task = asyncio.ensure_future(_speedtest(future, mirror, murl))
            tasks.append(task)
        # Waiting for fastest mirror (future result is set).
        await future
        for task in tasks:
            task.cancel("Fastest mirror found.")
        fastest = future.result()
        if fastest == C_INTMAX:
            return ("official", mlist.get("official", valtype=str))
        return fastest
    except KeyError:
        return ("official", host)


def get_url(remote: str, protocol: str = "http") -> str:
    """Get the mirror URL of a remote Git repository.

    Args:
        remote (str): The remote URL.
        protocol (str, optional): The protocol to use. Defaults to "http".

    Returns:
        str: The mirror URL.
    """

    logger.debug("Getting mirror of: %s ", remote)

    matched = re.match(
        r"(.*)/(.*)@(.*)",
        remote,
    )  # user/repo@website.
    if matched:
        user, repo, website = matched.groups()
        mirror = asyncio.run(find_fastest_mirror(website))
        try:
            url_template = (
                mirrorlist.get(website, valtype=dict)
                .get(protocol, valtype=dict)
                .get(mirror, valtype=str)
            )
            logger.info("Selected mirror: %s ('%s')", mirror, url_template)
            return format_str(url_template, fmt={"user": user, "repo": repo})
        except KeyError:
            logger.warning("Mirror not found: %s", mirror[0], exc_info=True)
    return remote


if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    from repoutils.shared.ktrigger import bind_ktrigger_interface

    class _TestKTrigger(IKernelTrigger):
        console_lines: dict[str, int]

        def __init__(self):
            super().__init__()
            self.console_lines = {}

        def pre_speedtest(self, host: str):
            self.console_lines[host] = (
                max(
                    self.console_lines.values(),
                    default=0,
                )
                + 1
            )
            print(f"Testing {host} ...", end="\n")

        def post_speedtest(self, host: str, speed: int):
            jump = (
                max(
                    self.console_lines.values(),
                    default=0,
                )
                - self.console_lines[host]
            )
            print(f"\x1b[{jump+1}A", end="")
            speed_str = (
                f"{speed} us" if speed != -1 else "\x1b[31mCANCELED\x1b[0m"
            )  # noqa: E501
            print(f"Testing {host} {speed_str}", end="\n")  # noqa: E501
            print(f"\x1b[{jump}B", end="")
            del self.console_lines[host]

    kt = _TestKTrigger()
    bind_ktrigger_interface("Test", kt)

    # Test: Find the fastest mirror.
    print(asyncio.run(find_fastest_mirror("github")))

    # Test: Get the mirror URL.
    url_ = get_url("cppp-project/cppp-repoutils@github")
    print(url_)
