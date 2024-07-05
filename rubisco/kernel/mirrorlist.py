# -*- coding: utf-8 -*-
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

"""
Git URL parser that supports mirrorlist.
e.g:
    "https://github.com/${{ user }}/${{ repo }}.git"
"""

import asyncio
import re

import json5 as json
from urllib3.util import parse_url

from rubisco.config import (DEFAULT_CHARSET, GLOBAL_CONFIG_DIR,
                            USER_CONFIG_DIR, WORKSPACE_CONFIG_DIR)
from rubisco.lib.exceptions import RUValueException
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.speedtest import C_INTMAX, url_speedtest
from rubisco.lib.variable import AutoFormatDict, format_str
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

__all__ = ["get_url"]

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
                file_data: dict = json.load(f)
                lower_data = {
                    k.lower() if isinstance(k, str) else k: v
                    for k, v in file_data.items()
                }
                mirrorlist.merge(lower_data)
        except (OSError, json.JSON5DecodeError) as exc_:
            logger.warning(
                "Failed to load mirrorlist file: %s: %s", mirrorlist_file, exc_
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


def get_mirrorlist(
    host: str,
    protocol: str = "http",
) -> AutoFormatDict:
    """Get the mirrorlist of a host.

    Args:
        host (str): The host you want to find.
        protocol (str): Connection protocol. Defaults to "http".
            We only support HTTP(s) for now.

    Returns:
        dict: The mirrorlist.
    """

    host = host.lower()

    mlist1 = mirrorlist.get(host, valtype=dict | str)
    if isinstance(mlist1, str):  # Alias support.
        mlist1 = mirrorlist.get(mlist1, valtype=dict | str)
    if isinstance(mlist1, str):
        try:
            return get_mirrorlist(mlist1, protocol)
        except RecursionError as exc:  # The easiest way to detect recursion :)
            raise RUValueException(
                format_str(
                    _("Recursion detected in mirrorlist: '${{name}}'"),
                    fmt={"name": mlist1},
                ),
                hint=_(
                    "Please check your mirrorlist.json file in"
                    "workspace, user or global config directory.",
                ),
            ) from exc
    return mlist1.get(protocol, valtype=dict)


async def find_fastest_mirror(
    host: str,
    protocol: str = "http",
) -> str:
    """Find the fastest mirror in mirrorlist.

    Args:
        host (str): The host you want to find.
        protocol (str): Connection protocol. Defaults to "http".
            We only support HTTP(s) for now.

    Returns:
        str: The mirror name.
    """

    try:
        mlist: AutoFormatDict = get_mirrorlist(host, protocol)
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
            return "official"
        return fastest
    except KeyError:
        return "official"


def get_url(
    remote: str,
    protocol: str = "http",
    use_fastest: bool = True,
) -> str:
    """Get the mirror URL of a remote Git repository.

    Args:
        remote (str): The remote URL.
        protocol (str, optional): The protocol to use. Defaults to "http".
        use_fastest (bool, optional): Use the fastest mirror. Defaults to True.

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
        if use_fastest:
            mirror = asyncio.run(find_fastest_mirror(website))
        else:
            mirror = "official"
        try:
            url_template = get_mirrorlist(website, protocol).get(
                mirror,
                valtype=str,
            )
            logger.info("Selected mirror: %s ('%s')", mirror, url_template)
            return format_str(url_template, fmt={"user": user, "repo": repo})
        except KeyError:
            logger.critical("Website not found: %s", mirror, exc_info=True)
            message = format_str(
                _("Source '${{protocol}}/${{website}}/${{name}}' not found."),
                fmt={
                    "website": website,
                    "protocol": protocol,
                    "name": mirror,
                },
            )
            raise RUValueException(message) from None
    return remote


if __name__ == "__main__":
    import rich

    from rubisco.shared.ktrigger import \
        bind_ktrigger_interface  # pylint: disable=ungrouped-imports

    rich.print(f"{__file__}: {__doc__.strip()}")

    class _TestKTrigger(IKernelTrigger):

        def pre_speedtest(self, host: str):
            rich.print(f"[blue]=>[/blue] Testing {host} ...", end="\n")

        def post_speedtest(self, host: str, speed: int):
            speed_str = f"{speed} us" if speed != -1 else " - CANCELED"
            rich.print(f"[blue]::[/blue] Testing {host} {speed_str}", end="\n")

    kt = _TestKTrigger()
    bind_ktrigger_interface("Test", kt)

    # Test: Find the fastest mirror.
    rich.print(asyncio.run(find_fastest_mirror("github")))

    # Test: Get the mirror URL.
    url_ = get_url("cppp-project/rubisco@github")
    rich.print(url_)

    # Test: Get a non-exist mirror URL.
    try:
        url_ = get_url("cppp-project/rubisco@non-exist")
        assert False
    except ValueError as exc_:
        rich.print(f"[green]Exception caught: {exc_}[/green]")
