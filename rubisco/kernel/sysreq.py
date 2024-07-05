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
System requirements slover and checker.
Detects the system package manager and installs the required packages.
"""

import ctypes
import os
import platform

from rubisco.config import DEFAULT_CHARSET
from rubisco.lib.command import command
from rubisco.lib.exceptions import RUShellExecutionException
from rubisco.lib.fileutil import find_command
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.process import Process, popen
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

# Detect OS.
OS: str | None = None
if platform.system() == "Windows":
    OS = "Windows"
elif platform.system() == "Linux":
    OS = "Linux"
elif platform.system() == "Darwin":
    OS = "macOS"
elif "BSD" in platform.system():
    OS = "BSD"

logger.info("Detected OS: %s", OS)

# Detect OS distribution.
DISTRIBUTION: str | None = None
if OS == "Linux":  # Only Linux has a lots of distributions.
    try:
        os_release = platform.freedesktop_os_release()
        DISTRIBUTION = os_release["ID"]
    except OSError:
        logger.warning(
            "Failed to detect distribution by '/etc/os-release'.",
            exc_info=True,
        )
        # Try to detect distribution by '/etc/issue.
        try:
            with open("/etc/issue", encoding=DEFAULT_CHARSET) as file:
                DISTRIBUTION = file.readline().strip()[0].lower()
        except (OSError, IndexError):
            logger.warning(
                "Failed to detect distribution by '/etc/issue'.", exc_info=True
            )
            # Try to detect distribution by 'lsb_release'.
            try:
                stdout, stderr, retcode = popen(
                    ["lsb_release", "-is"],
                    stdout=True,
                    stderr=False,
                )
                DISTRIBUTION = stdout.strip().lower()
            except OSError:
                logger.warning(
                    "Failed to detect distribution by 'lsb_release'.",
                    exc_info=True,
                )

logger.info("Detected distribution: %s", DISTRIBUTION)

# Detect package manager.
linux_supported_list = [
    # System official package managers.
    "apt",  # Debian/Ubuntu
    "apt-get"  # Debian/Ubuntu
    "dnf",  # Fedora
    "yum",  # CentOS/RHEL
    "zypper",  # openSUSE
    "pacman",  # ArchLinux
    "emerge",  # Gentoo
    "apk",  # Alpine
    # User-friendly package managers.
    "snap",  # Snapcraft
    "flatpak",  # Flatpak
    "nix",  # Nix
    "guix",  # Guix
    "brew",  # Linuxbrew
]

macos_supported_list = [
    "brew",  # Homebrew
    "macports",  # MacPorts
]

windows_supported_list = [
    "choco",  # Chocolatey
    "scoop",  # Scoop
    "winget",  # Windows Package Manager
]

bsd_supported_list = [
    "pkg",  # FreeBSD
    "pkg_add",  # OpenBSD
    "pkgin",  # NetBSD
]


# The package manager.
PACKAGE_MANAGER: str | None = None
PACKAGE_MANAGER_ID: str | None = None
find_list: list[str]
if OS == "Linux":
    match DISTRIBUTION:
        case "debian":
            find_list = ["apt"] + linux_supported_list
        case "ubuntu":
            find_list = ["apt"] + linux_supported_list
        case "fedora":
            find_list = ["dnf"] + linux_supported_list
        case "centos":
            find_list = ["yum"] + linux_supported_list
        case "rhel":
            find_list = ["yum"] + linux_supported_list
        case "opensuse":
            find_list = ["zypper"] + linux_supported_list
        case "arch":
            find_list = ["pacman"] + linux_supported_list
        case "gentoo":
            find_list = ["emerge"] + linux_supported_list
        case "alpine":
            find_list = ["apk"] + linux_supported_list
        case _:
            logger.warning("Unsupported distribution: %s", DISTRIBUTION)
            find_list = linux_supported_list
elif OS == "macOS":
    find_list = macos_supported_list
elif OS == "Windows":
    find_list = windows_supported_list
elif OS == "BSD":
    find_list = bsd_supported_list
else:
    logger.warning("Unsupported OS: %s", OS)

for package_manager in find_list:
    path = find_command(package_manager)
    if path != package_manager:
        PACKAGE_MANAGER_ID = package_manager
        PACKAGE_MANAGER = path
        break
else:
    logger.warning(_("No supported package manager found."))

logger.info(
    "Detected package manager '%s': %s",
    PACKAGE_MANAGER_ID,
    PACKAGE_MANAGER,
)


def is_root() -> bool:
    """
    Check if the current user is root.
    """

    if os.name == "nt":
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    return os.geteuid() == 0


def sudo(cmd: list[str]) -> str:
    """Run a command with elevated privileges.

    Args:
        cmd (list[str]): The command to run.

    Raises:
        RUShellExecutionException: If gsudo not found on Windows.

    Returns:
        str: The command to run with elevated privileges.
    """

    if is_root():
        return command(cmd)
    if os.name == "nt":
        if find_command("gsudo") == "gsudo":
            raise RUShellExecutionException(
                _("gsudo is required to run commands."),  # noqa: E501
                retcode=RUShellExecutionException.RETCODE_COMMAND_NOT_FOUND,  # noqa: E501
                docurl="https://gerardog.github.io/gsudo/docs/install",
            )

        return command(["gsudo"] + cmd)
    return command(["sudo"] + cmd)


def package_install(packages: list[str]):
    """Install packages using the package manager.

    Args:
        packages (list[str]): The packages to install.
    """

    if not PACKAGE_MANAGER:
        logger.warning(_("No supported system package manager found."))
        call_ktrigger(
            IKernelTrigger.on_syspkg_installation_skip,
            packages=packages,
            message=_("No supported system package manager found."),
        )
        return

    # Some package managers' install command is not 'install'.
    install_command: str
    match PACKAGE_MANAGER_ID:
        case "pacman":
            install_command = "-S"
        case "emerge":
            install_command = "--ask"
        case "apk":
            install_command = "add"
        case _:
            install_command = "install"

    # Some package managers' need to update the package list before installing.
    update_command: str
    match PACKAGE_MANAGER_ID:
        case "dnf":
            update_command = "makecache"
        case "yum":
            update_command = "makecache"
        case "zypper":
            update_command = "refresh"
        case "pacman":
            update_command = "-Sy"
        case "emerge":
            update_command = "--sync"
        case _:
            update_command = "update"

    Process(sudo([PACKAGE_MANAGER, update_command])).run()
    Process(sudo([PACKAGE_MANAGER, install_command] + packages)).run()
    logger.info("Installed packages: %s", packages)


if __name__ == "__main__":
    import sys

    import rich

    rich.print(f"{__file__}: {__doc__.strip()}")

    rich.print("OS: ", OS)
    rich.print("DISTRIBUTION: ", DISTRIBUTION)
    rich.print("PACKAGE_MANAGER: ", PACKAGE_MANAGER)
    rich.print("PACKAGE_MANAGER_ID: ", PACKAGE_MANAGER_ID)
    rich.print("is_root(): ", is_root())

    if "--debug-test-install" in sys.argv:
        # Test installation onlly if the script is run in debug mode. (For CI)
        package_install(["git"])
