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
from typing import TYPE_CHECKING, Any

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
from rubisco.kernel.command_event.args import (
    Argument,
    DynamicArguments,
    Option,
    load_callback_args,
)
from rubisco.kernel.command_event.callback import EventCallback
from rubisco.kernel.command_event.event_file_data import EventFileData
from rubisco.kernel.command_event.event_path import EventPath
from rubisco.lib.convert import convert_to
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.variable.fast_format_str import fast_format_str
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

if TYPE_CHECKING:
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


def list_packages(
    options: list[Option[Any]],
    args: list[Argument[Any]],
) -> None:
    """For 'rubisco ext list PATTERNS' command.

    Args:
        options (list[Option[Any]]): List of options.
        args (list[Argument[Any]]): List of arguments.

    """
    opts, args_ = load_callback_args(options, args)
    patterns: list[str] = args_
    show_workspace: bool = convert_to(opts["show-workspace"], bool)
    show_user: bool = convert_to(opts["show-user"], bool)
    show_global: bool = convert_to(opts["show-global"], bool)

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


def show_packages(
    options: list[Option[Any]],
    args: list[Argument[Any]],
) -> None:
    """For 'rubisco ext show PATTERNS' command.

    Args:
        options (list[Option[Any]]): List of options.
        args (list[Argument[Any]]): List of arguments.

    """
    opts, args_ = load_callback_args(options, args)
    patterns: list[str] = args_
    show_workspace: bool = convert_to(opts["show-workspace"], bool)
    show_user: bool = convert_to(opts["show-user"], bool)
    show_global: bool = convert_to(opts["show-global"], bool)

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


def install_packages(
    options: list[Option[Any]],
    args: list[Argument[Any]],
) -> None:
    """For 'rubisco ext install FILES' command.

    Args:
        options (list[Option[Any]]): List of options.
        args (list[Argument[Any]]): List of arguments.

    """
    opts, args_ = load_callback_args(options, args)
    files_glob: list[str] = args_
    files_list: list[Path] = []

    inst_to_global: bool = convert_to(opts["global"], bool)
    inst_to_user: bool = convert_to(opts["user"], bool)
    inst_to_workspace: bool = convert_to(opts["workspace"], bool)

    # Checking for conflicts.
    _sum = int(inst_to_global) + int(inst_to_user) + int(inst_to_workspace)
    if _sum > 1 or _sum == 0:
        msg = _("You must specify only one install destination.")
        raise RUValueError(msg)

    if inst_to_global:
        install_dest = GLOBAL_ENV
    elif inst_to_user:
        install_dest = USER_ENV
    else:
        install_dest = WORKSPACE_ENV

    for file_glob in files_glob:
        files_list.extend(Path.cwd().glob(file_glob))

    if not files_list:
        logger.info("No files found.")
        call_ktrigger(IKernelTrigger.on_hint, message=_("No files found."))
        return

    for file in files_list:
        install_extension(file, install_dest)


def uninstall_packages(
    options: list[Option[Any]],
    args: list[Argument[Any]],
) -> None:
    """For 'rubisco ext uninstall PATTERNS' command.

    Args:
        options (list[Option[Any]]): List of options.
        args (list[Argument[Any]]): List of arguments.

    """
    opts, args_ = load_callback_args(options, args)
    patterns: list[str] = args_
    uninst_global: bool = convert_to(opts["global"], bool)
    uninst_user: bool = convert_to(opts["user"], bool)
    uninst_workspace: bool = convert_to(opts["workspace"], bool)

    # Checking for conflicts.
    _sum = int(uninst_global) + int(uninst_user) + int(uninst_workspace)
    if _sum > 1 or _sum == 0:
        msg = _("You must specify only one uninstall destination.")
        raise RUValueError(msg)

    if uninst_global:
        env = GLOBAL_ENV
    elif uninst_user:
        env = USER_ENV
    else:
        env = WORKSPACE_ENV

    uninstall_extension(patterns, env)


def register_extman_cmds() -> None:
    """Register extension manager commands."""
    # Command "ext list".
    EventPath("/ext/list").mkfile(
        EventFileData(
            args=DynamicArguments(
                name="patterns",
                title=_("Packages matching patterns."),
                description=_("Packages matching patterns."),
                mincount=0,
            ),
            callbacks=[
                EventCallback(
                    callback=list_packages,
                    description=_(
                        "Default callback for list Rubisco extensions.",
                    ),
                ),
            ],
        ),
        description=_("Show project information."),
        options=[
            Option[bool](
                name="show-workspace",
                title=_("Show workspace extensions."),
                description=_("Show workspace extensions."),
                typecheck=bool,
                default=True,
                ext_attributes={
                    "cli-advanced-options": [
                        {
                            "name": "-w",
                            "description": _("Show workspace extensions."),
                            "action": "store_true",
                        },
                        {
                            "name": "-W",
                            "description": _("Hide workspace extensions."),
                            "action": "store_false",
                        },
                    ],
                },
            ),
            Option[bool](
                name="show-user",
                title=_("Show user extensions."),
                description=_("Show user extensions."),
                typecheck=bool,
                default=True,
                ext_attributes={
                    "cli-advanced-options": [
                        {
                            "name": "-u",
                            "description": _("Show user extensions."),
                            "action": "store_true",
                        },
                        {
                            "name": "-U",
                            "description": _("Hide user extensions."),
                            "action": "store_false",
                        },
                    ],
                },
            ),
            Option[bool](
                name="show-global",
                title=_("Show global extensions."),
                description=_("Show global extensions."),
                typecheck=bool,
                default=True,
                ext_attributes={
                    "cli-advanced-options": [
                        {
                            "name": "-g",
                            "description": _("Show global extensions."),
                            "action": "store_true",
                        },
                        {
                            "name": "-G",
                            "description": _("Hide global extensions."),
                            "action": "store_false",
                        },
                    ],
                },
            ),
        ],
    )

    # Command "ext show".
    EventPath("/ext/show").mkfile(
        EventFileData(
            args=DynamicArguments(
                name="packages",
                title=_("Packages matching patterns."),
                description=_("Packages matching patterns."),
                mincount=0,
            ),
            callbacks=[
                EventCallback(
                    callback=show_packages,
                    description=_(
                        "Default callback for show Rubisco extensions.",
                    ),
                ),
            ],
        ),
        description=_("Show extensions info with matching patterns."),
        options=[
            Option(
                name="show-workspace",
                aliases=["W"],
                title=_("Show workspace extensions."),
                description=_("Show workspace extensions."),
                typecheck=str,
                default=True,
            ),
            Option(
                name="show-user",
                aliases=["U"],
                title=_("Show user extensions."),
                description=_("Show user extensions."),
                typecheck=str,
                default=True,
            ),
            Option(
                name="show-global",
                aliases=["G"],
                title=_("Show global extensions."),
                description=_("Show global extensions."),
                typecheck=str,
                default=True,
            ),
        ],
    )

    # Command "ext install".
    EventPath("/ext/install").mkfile(
        EventFileData(
            args=DynamicArguments(
                name="files",
                title=_("Extension package files glob patterns."),
                description=_("Extension package files glob patterns."),
                mincount=1,
            ),
            callbacks=[
                EventCallback(
                    callback=install_packages,
                    description=_(
                        "Default callback for install Rubisco extensions.",
                    ),
                ),
            ],
        ),
        description=_("Install extensions with matching patterns."),
        options=[
            Option(
                name="workspace",
                aliases=["W"],
                title=_("Install to workspace."),
                description=_("Install extension packages to workspace."),
                typecheck=str,
                default="False",
            ),
            Option(
                name="user",
                aliases=["U"],
                title=_("Install to user."),
                description=_("Install extension packages to user."),
                typecheck=str,
                default="False",
            ),
            Option(
                name="global",
                aliases=["G"],
                title=_("Install to global."),
                description=_("Install extension packages to global."),
                typecheck=str,
                default="False",
            ),
        ],
    )

    # Command "ext uninstall".
    EventPath("/ext/uninstall").mkfile(
        EventFileData(
            args=DynamicArguments(
                name="packages",
                title=_("Packages matching patterns."),
                description=_("Packages matching patterns."),
                mincount=1,
            ),
            callbacks=[
                EventCallback(
                    callback=uninstall_packages,
                    description=_(
                        "Default callback for uninstall Rubisco extensions.",
                    ),
                ),
            ],
        ),
        description=_("Uninstall extensions with matching patterns."),
        options=[
            Option(
                name="workspace",
                aliases=["W"],
                title=_("Uninstall from workspace."),
                description=_("Uninstall extension packages from workspace."),
                typecheck=str,
                default="False",
            ),
            Option(
                name="user",
                aliases=["U"],
                title=_("Uninstall from user."),
                description=_("Uninstall extension packages from user."),
                typecheck=str,
                default="False",
            ),
            Option(
                name="global",
                aliases=["G"],
                title=_("Uninstall from global."),
                description=_("Uninstall extension packages from global."),
                typecheck=str,
                default="False",
            ),
        ],
    )
