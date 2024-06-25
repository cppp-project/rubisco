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
C++ Plus Repoutils CLI main entry point.
"""

import argparse
import atexit
import sys
from pathlib import Path

import colorama
import rich
import rich.live
import rich.progress

from repoutils.cli.input import ask_yesno
from repoutils.cli.output import (output_error, output_hint, output_step,
                                  output_warning, pop_level, push_level,
                                  show_exception)
from repoutils.config import APP_NAME, APP_VERSION, USER_REPO_CONFIG
from repoutils.kernel.log_clean import clean_log
from repoutils.kernel.project_config import (ProjectConfigration,
                                             load_project_config)
from repoutils.kernel.workflow import Step, Workflow
from repoutils.lib.exceptions import RUValueException
from repoutils.lib.l10n import _
from repoutils.lib.log import logger
from repoutils.lib.process import Process
from repoutils.lib.variable import format_str, make_pretty
from repoutils.shared.extention import IRUExtention
from repoutils.shared.ktrigger import IKernelTrigger, bind_ktrigger_interface

arg_parser = argparse.ArgumentParser(
    description=_("Repoutils CLI"),
    formatter_class=argparse.RawDescriptionHelpFormatter,
)

arg_parser.add_argument(
    "-v",
    "--version",
    action="store_true",
    help=_("Show version infomation."),
)

arg_parser.add_argument(
    "--debug",
    action="store_true",
    help=_("Run repoutils in debug mode."),
)

arg_parser.add_argument(
    "command",
    action="append",
    type=str,
    help=_("Run a command defined by project or extention."),
)


def show_version() -> None:
    """
    Show version.
    """

    print(APP_NAME, end=" ")
    print(str(APP_VERSION))

    rich.print(_("Copyright (C) 2024 The C++ Plus Project."))
    rich.print(
        _(
            "License [bold]GPLv3+[/bold]: GNU GPL version [cyan]3"
            "[/cyan] or later <https://www.gnu.org/licenses/gpl.html>."
        )
    )
    rich.print(
        _(
            "This is free software: you are free to change and redistribute it."  # noqa: E501
        )
    )
    rich.print(
        _(
            "There is [yellow]NO WARRANTY[/yellow], to the extent permitted by law.",  # noqa: E501
        )
    )
    rich.print(_("Written by [underline]ChenPi11[/underline]."))


project_config: ProjectConfigration | None = None


class RepoutilsKTrigger(  # pylint: disable=too-many-public-methods
    IKernelTrigger
):  # Repoutils CLI kernel trigger.
    """Repoutils kernel trigger."""

    cur_progress: rich.progress.Progress | None = None
    tasks: dict[str, rich.progress.TaskID] = {}
    live: rich.live.Live | None = None
    _speedtest_hosts: dict[str, str] = {}

    def pre_exec_process(self, proc: Process):
        output_step(f"Executing: [cyan]{proc.origin_cmd}[/cyan] ...")
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

        if task_name in self.tasks:
            self.cur_progress.update(self.tasks[task_name], completed=0)
        if self.cur_progress is None:
            self.cur_progress = rich.progress.Progress()
            self.cur_progress.start()
        task_id = self.cur_progress.add_task(title, total=total)
        self.tasks[task_name] = task_id

    def on_progress(
        self,
        task_name: str,
        current: int | float,
        delta: bool = False,
    ):
        if delta:
            self.cur_progress.update(self.tasks[task_name], advance=current)
        else:
            self.cur_progress.update(self.tasks[task_name], completed=current)

    def set_progress_total(self, task_name: str, total: int | float):
        self.cur_progress.update(self.tasks[task_name], total=total)

    def on_finish_task(self, task_name: str):
        self.cur_progress.remove_task(self.tasks[task_name])
        del self.tasks[task_name]
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
                        "Running: ${{name}} [black](${{id}})[/black]",
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
                    "Running workflow: ${{name}} [black](${{id}})[/black]",
                ),
                fmt={"name": workflow.name, "id": workflow.id},
            )
        )
        push_level()

    def post_run_workflow(self, workflow: Workflow) -> None:
        pop_level()

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
                _("Loaded extension: ${{name}} ..."),
                fmt={"name": instance.name},
            )
        )


def on_exit():
    """
    Reset terminal color.
    """

    print(colorama.Fore.RESET, end="", flush=True)


atexit.register(on_exit)

hooks: dict[str, list] = {}


def bind_hook(name: str):
    """Bind hook to a command.

    Args:
        name (str): Hook name.
    """

    if project_config and name in project_config.hooks.keys():
        hooks[name] = project_config.hooks[name]


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
    hooks[name].run()


def load_project():
    """
    Load the project in cwd.
    """

    global project_config  # pylint: disable=global-statement

    try:
        project_config = load_project_config(Path.cwd())
        for hook_name in project_config.hooks.keys():  # Bind all hooks.
            bind_hook(hook_name)
    except FileNotFoundError as exc:
        raise RUValueException(
            format_str(
                _(
                    "Working directory '[underline]${{path}}[/underline]'"
                    " not a repoutils project."
                ),
                fmt={"path": make_pretty(Path.cwd().absolute())},
            ),
            hint=format_str(
                _("'[underline]${{path}}[/underline] is not found."),
                fmt={"path": make_pretty(USER_REPO_CONFIG.absolute())},
            ),
        ) from exc


def main() -> None:
    """Main entry point."""

    try:
        logger.info("Repoutils CLI version %s started.", str(APP_VERSION))

        colorama.init()
        clean_log()

        bind_ktrigger_interface("repoutils", RepoutilsKTrigger())

        args = arg_parser.parse_args()

        if args.version:
            show_version()
            return

        load_project()

        op_command = args.command[0]
        call_hook(op_command)

    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.critical("An unexpected error occurred.", exc_info=True)
        show_exception(exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
