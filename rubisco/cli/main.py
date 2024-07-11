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
C++ Plus Rubisco CLI main entry point.
"""

import argparse
import atexit
import sys
from pathlib import Path
from typing import Any, Iterable

import colorama
import rich
import rich.live
import rich.progress
from rich_argparse import RichHelpFormatter

from rubisco.cli.input import ask_yesno
from rubisco.cli.output import (output_error, output_hint, output_step,
                                output_warning, pop_level, push_level,
                                show_exception)
from rubisco.config import (APP_NAME, APP_VERSION, DEFAULT_CHARSET,
                            DEFAULT_LOG_KEEP_LINES, LOG_FILE, USER_REPO_CONFIG)
from rubisco.kernel.project_config import ProjectConfigration  # noqa: E501
from rubisco.kernel.project_config import load_project_config
from rubisco.kernel.workflow import Step, Workflow
from rubisco.lib.exceptions import RUValueException
from rubisco.lib.l10n import _, locale_language, locale_language_name
from rubisco.lib.log import logger
from rubisco.lib.process import Process
from rubisco.lib.variable import format_str, make_pretty
from rubisco.shared.extention import IRUExtention, load_all_extentions
from rubisco.shared.ktrigger import (IKernelTrigger, bind_ktrigger_interface,
                                     call_ktrigger)

__all__ = ["main"]


def show_version() -> str:
    """
    Get version string.
    """

    rich.print(APP_NAME, end=" ")
    print(str(APP_VERSION))
    rich.print(
        _("Copyright (C) 2024 The C++ Plus Project."),
    )
    rich.print(
        _(
            "License [bold]GPLv3+[/bold]: GNU GPL version [cyan]3"
            "[/cyan] or later <https://www.gnu.org/licenses/gpl.html>."
        ),
    )
    rich.print(
        _(
            "This is free software: you are free to change and redistribute it."  # noqa: E501
        ),
    )
    rich.print(
        _(
            "There is [yellow]NO WARRANTY[/yellow], to the extent permitted by law.",  # noqa: E501
        ),
    )
    rich.print(
        _("Written by [underline]ChenPi11[/underline]."),
    )


class _VersionAction(argparse.Action):
    """
    Version Action for rubisco.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        option_strings,
        version=None,
        dest=argparse.SUPPRESS,
        default=argparse.SUPPRESS,
        help=None,
    ):  # pylint: disable=redefined-builtin
        if help is None:
            help = _("Show program's version number and exit.")
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help,
        )
        self.version = version

    def __call__(self, parser, namespace, values, option_string=None):
        show_version()
        parser.exit()


hooks: dict[str, list] = {}


class RUHelpFormatter(RichHelpFormatter):
    """Rubisco CLI help formatter."""

    def add_usage(
        self,
        usage: str | None,
        actions: Iterable[argparse.Action],
        groups: Iterable[argparse._MutuallyExclusiveGroup],
        prefix: str | None = None,
    ):
        for action in actions:
            if action.help == "show this help message and exit":
                action.help = _("Show this help message and exit.")

        super().add_usage(usage, actions, groups, prefix)

    def format_help(self) -> str:
        help_str = super().format_help()
        help_str = help_str.replace("Usage:", _("Usage:"))
        help_str = help_str.replace(
            "Positional Arguments:",
            _("Positional Arguments:"),
        )

        help_str = help_str.replace("Options:", _("Options:"))

        return help_str


arg_parser = argparse.ArgumentParser(
    description="Rubisco CLI",
    formatter_class=RUHelpFormatter,
)

arg_parser.register("action", "version", _VersionAction)

arg_parser.add_argument(
    "-v",
    "--version",
    action="version",
    version="",
)

arg_parser.add_argument(
    "--debug",
    action="store_true",
    help=_("Run rubisco in debug mode."),
)

arg_parser.add_argument(
    "command",
    action="store",
    nargs=1,
    help=_("Command to run."),
)

hook_commands = arg_parser.add_subparsers(
    title=_("Available commands"),
    dest="command",
    metavar="",
)

hook_commands.add_parser(
    "info",
    help=_("Show project information."),
)

project_config: ProjectConfigration | None = None


class RubiscoKTrigger(  # pylint: disable=too-many-public-methods
    IKernelTrigger
):  # Rubisco CLI kernel trigger.
    """Rubisco kernel trigger."""

    cur_progress: rich.progress.Progress | None = None
    tasks: dict[str, rich.progress.TaskID] = {}
    task_types: dict[str, int] = {}
    task_totals: dict[str, int] = {}
    live: rich.live.Live | None = None
    _speedtest_hosts: dict[str, str] = {}

    def pre_exec_process(self, proc: Process):
        output_step(
            format_str(
                _("Executing: [cyan]${{cmd}}[/cyan] ..."),
                fmt={"cmd": proc.origin_cmd.strip()},
            )
        )
        print(colorama.Fore.LIGHTBLACK_EX, end="", flush=True)

    def post_exec_process(
        self,
        proc: Process,
        retcode: int,
        raise_exc: bool,
    ) -> None:
        print(colorama.Fore.RESET, end="", flush=True)

    def file_exists(self, path: Path):
        if not ask_yesno(
            format_str(
                _(
                    "File '[underline]${{path}}[/underline]' already exists."
                    " [yellow]Overwrite[/yellow]?"
                ),
                fmt={"path": make_pretty(path.absolute())},
            ),
            default=True,
        ):
            raise KeyboardInterrupt

    def on_new_task(
        self,
        task_name: str,
        task_type: int,
        total: int | float,
    ) -> None:
        output_step(task_name)

        if task_type == IKernelTrigger.TASK_DOWNLOAD:
            title = _("[yellow]Downloading[/yellow]")
        elif task_type == IKernelTrigger.TASK_EXTRACT:
            title = _("[yellow]Extracting[/yellow]")
        elif task_type == IKernelTrigger.TASK_COMPRESS:
            title = _("[yellow]Compressing[/yellow]")
        else:
            title = _("[yellow]Processing[/yellow]")

        if task_name in self.tasks:
            self.cur_progress.update(self.tasks[task_name], completed=0)
        if self.cur_progress is None:
            self.cur_progress = rich.progress.Progress()
            self.cur_progress.start()
        task_id = self.cur_progress.add_task(title, total=total)
        self.tasks[task_name] = task_id
        self.task_types[task_name] = task_type
        self.task_totals[task_name] = total

    def on_progress(
        self,
        task_name: str,
        current: int | float,
        delta: bool = False,
        more_data: dict[str, Any] | None = None,
    ):
        if (
            self.task_types[task_name] == IKernelTrigger.TASK_EXTRACT
            and self.task_totals[task_name] < 2500
        ):
            path = str((more_data["dest"] / more_data["path"]).absolute())
            rich.print(f"[underline]{path}[/underline]")
        if delta:
            self.cur_progress.update(self.tasks[task_name], advance=current)
        else:
            self.cur_progress.update(self.tasks[task_name], completed=current)

    def set_progress_total(self, task_name: str, total: int | float):
        self.cur_progress.update(self.tasks[task_name], total=total)

    def on_finish_task(self, task_name: str):
        self.cur_progress.remove_task(self.tasks[task_name])
        del self.tasks[task_name]
        del self.task_types[task_name]
        del self.task_totals[task_name]
        if not self.tasks:
            self.cur_progress.stop()
            self.cur_progress = None

    def on_syspkg_installation_skip(
        self,
        packages: list[str],
        message: str,
    ) -> None:
        output_warning(message)
        output_hint(
            format_str(
                _(
                    "Please install the following packages manually:"
                    " [bold]${{packages}}[/bold]."
                ),
                fmt={"packages": ", ".join(packages)},
            )
        )

        if not ask_yesno(_("Continue anyway?"), default=False):
            raise KeyboardInterrupt

    def on_update_git_repo(self, path: Path, branch: str) -> None:
        output_step(
            format_str(
                _(
                    "Updating Git repository '[underline]${{path}}[/underline]"
                    "'(${{branch}}) ...",
                ),
                fmt={"path": make_pretty(path), "branch": make_pretty(branch)},
            )
        )

    def on_clone_git_repo(
        self,
        url: str,
        path: Path,
        branch: str,
    ) -> None:
        output_step(
            format_str(
                _(
                    "Cloning Git repository ${{url}} (${{branch}}) into "
                    "'[underline]${{path}}[/underline]' ...",
                ),
                fmt={"url": url, " branch": branch, "path": make_pretty(path)},
            )
        )

    def on_warning(self, message: str) -> None:
        output_warning(message)

    def on_error(self, message: str) -> None:
        output_error(message)

    def _update_live(self):
        msg = ""
        for host_, status in self._speedtest_hosts.items():
            msg += format_str(
                _("Testing ${{host}}: ${{status}}\n"),
                fmt={"host": host_, "status": status},
            )
        msg = msg.strip()
        self.live.update(msg)

    def pre_speedtest(self, host: str):
        if self.live is None:
            output_step(_("Performing websites speed test ..."))
            self.live = rich.live.Live()
            self.live.start()
            self._speedtest_hosts.clear()
        self._speedtest_hosts[host] = _("[yellow]Testing[/yellow] ...")
        self._update_live()

    def post_speedtest(self, host: str, speed: int):
        if speed == -1:
            self._speedtest_hosts[host] = _("[red]Canceled[/red]")
        else:
            self._speedtest_hosts[host] = format_str(
                _("${{speed}} us"), fmt={"speed": speed}
            )

        self._update_live()

        cant_stop = False
        for status in self._speedtest_hosts.values():
            cant_stop = cant_stop or status == _(
                "[yellow]Testing[/yellow] ...",
            )

        if not cant_stop:
            self.live.stop()
            self.live = None

    def pre_run_workflow_step(self, step: Step) -> None:
        if step.name.strip():
            output_step(
                format_str(
                    _(
                        "Running: [white]${{name}}[/white] [black](${{id}})[/black]",  # noqa: E501
                    ),
                    fmt={"name": step.name, "id": step.id},
                )
            )
        push_level()

    def post_run_workflow_step(self, step: Step) -> None:
        pop_level()

    def pre_run_workflow(self, workflow: Workflow) -> None:
        output_step(
            format_str(
                _(
                    "Running workflow: [white]${{name}}[/white] "
                    "[black](${{id}})[/black]",
                ),
                fmt={"name": workflow.name, "id": workflow.id},
            )
        )
        push_level()

    def post_run_workflow(self, workflow: Workflow) -> None:
        pop_level()
        output_step(
            format_str(
                _("Workflow '${{name}}' finished."),
                fmt={"name": workflow.name},
            )
        )

    def on_mkdir(self, path: Path) -> None:
        output_step(
            format_str(
                _("Creating directory: [underline]${{path}}[/underline] ..."),
                fmt={"path": make_pretty(path.absolute())},
            )
        )

    def on_output(self, msg: str) -> None:
        rich.print(msg)

    def on_move_file(self, src: Path, dst: Path) -> None:
        output_step(
            format_str(
                _(
                    "Moving file '[underline]${{src}}[/underline]' to"
                    " '[underline]${{dst}}[/underline]' ...",
                ),
                fmt={
                    "src": make_pretty(src.absolute()),
                    "dst": make_pretty(dst.absolute()),
                },
            )
        )

    def on_copy(self, src: Path, dst: Path) -> None:
        output_step(
            format_str(
                _(
                    "Copying '[underline]${{src}}[/underline]' to"
                    " '[underline]${{dst}}[/underline]' ...",
                ),
                fmt={
                    "src": make_pretty(src.absolute()),
                    "dst": str(dst.absolute()),
                },
            )
        )

    def on_remove(self, path: Path) -> None:
        output_step(
            format_str(
                _("Removing '[underline]${{path}}[/underline]' ..."),
                fmt={"path": make_pretty(path.absolute())},
            )
        )

    def on_extention_loaded(self, instance: IRUExtention):
        output_step(
            format_str(
                _("Extension '${{name}}' loaded."),
                fmt={"name": instance.name},
            )
        )

    def on_show_project_info(self, project: ProjectConfigration):
        rich.print(
            format_str(
                _(
                    "Rubisco CLI language: '${{locale}}' '${{charset}}' '${{lang}}'",  # noqa: E501
                ),
                fmt={
                    "locale": locale_language(),
                    "charset": DEFAULT_CHARSET,
                    "lang": locale_language_name(),
                },
            )
        )
        rich.print(
            format_str(
                _("Project: ${{name}}"),
                fmt={"name": make_pretty(project.name)},
            ),
        )
        rich.print(
            format_str(
                _("Config file: [underline]${{path}}[/underline]"),
                fmt={"path": make_pretty(project.config_file)},
            )
        )
        rich.print(
            format_str(
                _("Version [white]${{version}}[/white]"),
                fmt={"version": str(project.version)},
            )
        )

        if isinstance(project.maintainer, list):
            maintainers = "\n  ".join(project.maintainer)
        else:
            maintainers = str(project.maintainer)
        rich.print(
            format_str(
                _("Maintainer: ${{maintainer}}"),
                fmt={"maintainer": maintainers},
            )
        )
        rich.print(
            format_str(
                _("License: ${{license}}"),
                fmt={"license": project.license},
            )
        )
        rich.print(
            format_str(
                _("Description: ${{desc}}"),
                fmt={"desc": project.description},
            )
        )


def on_exit():
    """
    Reset terminal color.
    """

    print(colorama.Fore.RESET, end="", flush=True)


atexit.register(on_exit)


def bind_hook(name: str):
    """Bind hook to a command.

    Args:
        name (str): Hook name.
    """

    logger.debug("Binding hook: %s", name)
    if project_config and name in project_config.hooks.keys():
        if name not in hooks:
            hooks[name] = []
        hooks[name].append(project_config.hooks[name])


def call_hook(name: str):
    """Call a hook.

    Args:
        name (str): The hook name.
    """

    if name not in hooks:
        raise RUValueException(
            format_str(
                _("Undefined command or hook ${{name}}"),
                fmt={"name": make_pretty(name)},
            ),
            hint=_("Perhaps a typo?"),
        )
    for hook in hooks[name]:
        hook.run()


def load_project():
    """
    Load the project in cwd.
    """

    global project_config  # pylint: disable=global-statement

    try:
        project_config = load_project_config(Path.cwd())
        for hook_name in project_config.hooks.keys():  # Bind all hooks.
            bind_hook(hook_name)
            hook_commands.add_parser(
                hook_name,
                help=format_str(
                    _("(${{num}} overrides)"),
                    fmt={"num": str(len(hooks[hook_name]))},
                ),
            )
    except FileNotFoundError as exc:
        raise RUValueException(
            format_str(
                _(
                    "Working directory '[underline]${{path}}[/underline]'"
                    " not a rubisco project."
                ),
                fmt={"path": make_pretty(Path.cwd().absolute())},
            ),
            hint=format_str(
                _("'[underline]${{path}}[/underline]' is not found."),
                fmt={"path": make_pretty(USER_REPO_CONFIG.absolute())},
            ),
        ) from exc


def clean_log():
    """
    Clean the log file.
    """

    try:
        line_count = 0
        with open(LOG_FILE, "r+", encoding=DEFAULT_CHARSET) as f:
            for _line in f:
                line_count += 1
                if line_count > DEFAULT_LOG_KEEP_LINES:
                    f.seek(0)
                    f.truncate()
                    return
    except:  # pylint: disable=bare-except  # noqa: E722
        logger.warning("Failed to clean log file.", exc_info=True)


def main() -> None:
    """Main entry point."""

    try:
        clean_log()
        logger.info("Rubisco CLI version %s started.", str(APP_VERSION))
        colorama.init()
        bind_ktrigger_interface("rubisco", RubiscoKTrigger())
        load_all_extentions()

        try:
            load_project()
        finally:
            args = arg_parser.parse_args()

        op_command = args.command[0]
        if op_command == "info":
            call_ktrigger(
                IKernelTrigger.on_show_project_info,
                project=project_config,
            )
        else:
            call_hook(op_command)

    except SystemExit as exc:
        raise exc from None  # Do not show traceback.
    except KeyboardInterrupt as exc:
        show_exception(exc)
        sys.exit(1)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.critical("An unexpected error occurred.", exc_info=True)
        show_exception(exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
