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

"""C++ Plus Rubisco extension manager command lines."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from rubisco.cli.main.arg_parser import extman_command_parser
from rubisco.cli.main.help_formatter import RUHelpFormatter
from rubisco.envutils.env import (
    GLOBAL_ENV,
    USER_ENV,
    WORKSPACE_ENV,
    RUEnvironment,
)
from rubisco.envutils.env_type import EnvType
from rubisco.envutils.packages import (
    install_extension,
    query_packages,
    uninstall_extension,
)
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

if TYPE_CHECKING:
    import argparse

    from rubisco.envutils.packages import ExtensionPackageInfo

__all__ = ["register_extman_cmds"]


def _get_envtype_str(env_type: EnvType) -> str:
    if env_type == EnvType.GLOBAL:
        return _("global")
    if env_type == EnvType.USER:
        return _("user")
    if env_type == EnvType.WORKSPACE:
        return _("workspace")
    if env_type == EnvType.FOREIGN:
        return _("foreign-package")
    return _("unknown")


def _list_pkgs(
    patterns: list[str],
    *,
    show_workspace: bool,
    show_user: bool,
    show_global: bool,
) -> list[ExtensionPackageInfo]:

    if not patterns:
        patterns = [".*"]

    envs: list[RUEnvironment] = []

    if GLOBAL_ENV.exists() and show_global:
        envs.append(GLOBAL_ENV)
    if USER_ENV.exists() and show_user:
        envs.append(USER_ENV)
    if WORKSPACE_ENV.exists() and show_workspace:
        envs.append(WORKSPACE_ENV)

    if not envs:
        call_ktrigger(
            IKernelTrigger.on_warning,
            message=_("No environment exists or selected."),
        )

    pkg_set = query_packages(patterns, envs)

    return list(pkg_set)


def list_packages(args: argparse.Namespace) -> None:
    """For 'rubisco ext list PATTERNS' command.

    Args:
        args (argparse.Namespace): Argparse arguments.

    """
    patterns: list[str] = args.packages
    show_workspace: bool = args.show_workspace
    show_user: bool = args.show_user
    show_global: bool = args.show_global

    pkg_list = _list_pkgs(
        patterns,
        show_workspace=show_workspace,
        show_user=show_user,
        show_global=show_global,
    )

    if not pkg_list:
        return
    for pkg in pkg_list:
        str_envname = _get_envtype_str(pkg.env_type)

        call_ktrigger(
            IKernelTrigger.on_output,
            message=f"[green]{pkg.name}[/green]/[bold]{str_envname}[/bold]"
            f" [cyan]{pkg.version:s}[/cyan]\n\t{pkg.description}",
        )


def _show_pkgs(pkg: ExtensionPackageInfo) -> None:
    call_ktrigger(
        IKernelTrigger.on_output,
        message=fast_format_str(
            _("Package: [green]${{name}}[/green]"),
            fmt={"name": pkg.name},
        ),
    )
    call_ktrigger(
        IKernelTrigger.on_output,
        message=fast_format_str(
            _("Version: [cyan]${{ver}}[/cyan]"),
            fmt={"ver": str(pkg.version)},
        ),
    )
    call_ktrigger(
        IKernelTrigger.on_output,
        message=fast_format_str(
            _("Installation Location: ${{loc}}"),
            fmt={"loc": _get_envtype_str(pkg.env_type)},
        ),
    )
    call_ktrigger(
        IKernelTrigger.on_output,
        message=fast_format_str(
            _("Maintainers: ${{maintainers}}"),
            fmt={"maintainers": ", ".join(pkg.maintainers)},
        ),
    )
    call_ktrigger(
        IKernelTrigger.on_output,
        message=fast_format_str(
            _("Homepage: ${{homepage}}"),
            fmt={"homepage": pkg.homepage},
        ),
    )
    call_ktrigger(
        IKernelTrigger.on_output,
        message=fast_format_str(
            _("License: ${{license}}"),
            fmt={"license": pkg.pkg_license},
        ),
    )
    call_ktrigger(
        IKernelTrigger.on_output,
        message=fast_format_str(
            _("Tags: ${{tags}}"),
            fmt={"tags": ", ".join(pkg.tags)},
        ),
    )
    call_ktrigger(
        IKernelTrigger.on_output,
        message=fast_format_str(
            _("Description: ${{desc}}"),
            fmt={"desc": pkg.description},
        ),
    )


def show_packages(args: argparse.Namespace) -> None:
    """For 'rubisco ext show PATTERNS' command.

    Args:
        args (argparse.Namespace): Argparse arguments.

    """
    patterns: list[str] = args.packages
    show_workspace: bool = args.show_workspace
    show_user: bool = args.show_user
    show_global: bool = args.show_global

    pkg_list = _list_pkgs(
        patterns,
        show_workspace=show_workspace,
        show_user=show_user,
        show_global=show_global,
    )

    if not pkg_list:
        call_ktrigger(IKernelTrigger.on_hint, message=_("No packages found."))
        return
    for pkg in pkg_list:
        _show_pkgs(pkg)
        if len(pkg_list) > 1:
            call_ktrigger(IKernelTrigger.on_output, message="")


def install_packages(args: argparse.Namespace) -> None:
    """For 'rubisco ext install FILES' command.

    Args:
        args (argparse.Namespace): Argparse arguments.

    """
    files_glob: list[str] = args.files
    install_dest_type: EnvType = args.install_dest
    files_list: list[Path] = []

    install_dest: RUEnvironment
    match install_dest_type:
        case EnvType.GLOBAL:
            install_dest = GLOBAL_ENV
        case EnvType.USER:
            install_dest = USER_ENV
        case EnvType.WORKSPACE:
            install_dest = WORKSPACE_ENV
        case _:
            msg = "Invalid install destination."
            raise ValueError(msg)

    for file_glob in files_glob:
        files_list.extend(Path.cwd().glob(file_glob))

    if not files_list:
        logger.info("No files found.")
        call_ktrigger(IKernelTrigger.on_hint, message=_("No files found."))
        return

    for file in files_list:
        install_extension(file, install_dest)


def uninstall_packages(args: argparse.Namespace) -> None:
    """For 'rubisco ext uninstall PATTERNS' command.

    Args:
        args (argparse.Namespace): Argparse arguments.

    """
    patterns: list[str] = args.packages
    env_type: EnvType = args.env_type

    env: RUEnvironment
    match env_type:
        case EnvType.GLOBAL:
            env = GLOBAL_ENV
        case EnvType.USER:
            env = USER_ENV
        case EnvType.WORKSPACE:
            env = WORKSPACE_ENV
        case _:
            msg = "Invalid uninstall destination."
            raise ValueError(msg)

    uninstall_extension(patterns, env)


def register_extman_cmds() -> None:
    """Register extension manager commands."""
    # Command "ext list".
    ext_list_command_parser = extman_command_parser.add_parser(
        "list",
        help=_("List extensions with matching patterns."),
        formatter_class=RUHelpFormatter,
    )

    ext_list_command_parser.add_argument(
        "packages",
        nargs="*",
        help=_("Packages matching patterns."),
    )

    ext_list_command_parser.set_defaults(func=list_packages)

    ext_list_command_parser.add_argument(
        "-W",
        "--ignore-workspace",
        "--no-workspace",
        action="store_false",
        dest="show_workspace",
        default=True,
        help=_("List extensions in workspace."),
    )

    ext_list_command_parser.add_argument(
        "-U",
        "--ignore-user",
        "--no-user",
        action="store_false",
        dest="show_user",
        default=True,
        help=_("List extensions in user."),
    )

    ext_list_command_parser.add_argument(
        "-G",
        "--ignore-global",
        "--no-global",
        action="store_false",
        dest="show_global",
        default=True,
        help=_("List extensions in global."),
    )

    # Command "ext show".
    ext_show_command_parser = extman_command_parser.add_parser(
        "show",
        help=_("Show extensions info with matching patterns."),
        formatter_class=RUHelpFormatter,
    )

    ext_show_command_parser.add_argument(
        "packages",
        nargs="*",
        help=_("Packages matching patterns."),
    )

    ext_show_command_parser.set_defaults(func=show_packages)

    ext_show_command_parser.add_argument(
        "-W",
        "--ignore-workspace",
        action="store_false",
        dest="show_workspace",
        default=True,
        help=_("List extensions in workspace."),
    )

    ext_show_command_parser.add_argument(
        "-U",
        "--ignore-user",
        action="store_false",
        dest="show_user",
        default=True,
        help=_("List extensions in user."),
    )

    ext_show_command_parser.add_argument(
        "-G",
        "--ignore-global",
        action="store_false",
        dest="show_global",
        default=True,
        help=_("List extensions in global."),
    )

    # Command "ext install".
    ext_install_command_parser = extman_command_parser.add_parser(
        "install",
        help=_("Install extensions with matching patterns."),
        formatter_class=RUHelpFormatter,
    )

    ext_install_command_parser.add_argument(
        "files",
        nargs="+",
        help=_("Extension package files glob patterns."),
    )

    ext_install_command_parser.set_defaults(func=install_packages)

    ext_install_command_parser.add_argument(
        "-w",
        "--workspace",
        action="store_const",
        dest="install_dest",
        const=EnvType.WORKSPACE,
        default=EnvType.WORKSPACE,
        help=_("Install extensions to workspace."),
    )

    ext_install_command_parser.add_argument(
        "-u",
        "--user",
        action="store_const",
        dest="install_dest",
        const=EnvType.USER,
        help=_("Install extensions to user."),
    )

    ext_install_command_parser.add_argument(
        "-g",
        "--global",
        action="store_const",
        dest="install_dest",
        const=EnvType.GLOBAL,
        help=_("Install extensions to global."),
    )

    # Command "ext uninstall".
    ext_uninstall_command_parser = extman_command_parser.add_parser(
        "uninstall",
        help=_("Uninstall extensions with matching patterns."),
        formatter_class=RUHelpFormatter,
    )

    ext_uninstall_command_parser.add_argument(
        "packages",
        nargs="+",
        help=_("Packages matching patterns."),
    )

    ext_uninstall_command_parser.set_defaults(func=uninstall_packages)

    ext_uninstall_command_parser.add_argument(
        "-w",
        "--workspace",
        action="store_const",
        dest="env_type",
        const=EnvType.WORKSPACE,
        default=EnvType.WORKSPACE,
        help=_("Uninstall extensions in workspace."),
    )

    ext_uninstall_command_parser.add_argument(
        "-u",
        "--user",
        action="store_const",
        dest="env_type",
        const=EnvType.USER,
        help=_("Uninstall extensions in user."),
    )

    ext_uninstall_command_parser.add_argument(
        "-g",
        "--global",
        action="store_const",
        dest="env_type",
        const=EnvType.GLOBAL,
        help=_("Uninstall extensions in global."),
    )
