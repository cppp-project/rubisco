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

"""C++ Plus Rubisco CLI main entry point."""

from __future__ import annotations

import argparse
import atexit
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import colorama
import rich
import rich.live
import rich.progress
from rich_argparse import RichHelpFormatter

from rubisco.cli.input import ask_yesno
from rubisco.cli.output import (
    get_prompt,
    output_error,
    output_hint,
    output_line,
    output_step,
    output_warning,
    pop_level,
    push_level,
    show_exception,
    sum_level_indent,
)
from rubisco.config import (
    APP_NAME,
    APP_VERSION,
    DEFAULT_CHARSET,
    DEFAULT_LOG_KEEP_LINES,
    LOG_FILE,
    PIP_LOG_FILE,
    USER_REPO_CONFIG,
)
from rubisco.kernel.project_config import (
    ProjectConfigration,
    load_project_config,
)
from rubisco.lib.exceptions import RUError, RUValueError
from rubisco.lib.l10n import _, locale_language, locale_language_name
from rubisco.lib.log import logger
from rubisco.lib.speedtest import C_INTMAX
from rubisco.lib.variable import format_str, make_pretty
from rubisco.shared.extension import IRUExtention, load_all_extensions
from rubisco.shared.ktrigger import (
    IKernelTrigger,
    bind_ktrigger_interface,
    call_ktrigger,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from rubisco.envutils.env import RUEnvironment
    from rubisco.kernel.workflow import Step, Workflow
    from rubisco.lib.process import Process
    from rubisco.lib.version import Version


__all__ = ["main"]


def show_version() -> None:
    """Get version string."""
    rich.print(APP_NAME, f"[white]{APP_VERSION}[/white]", end="\n")

    copyright_text = _(
        "Copyright (C) 2024 The C++ Plus Project.\n"
        "License [bold]GPLv3+[/bold]: GNU GPL version [cyan]3[/cyan] or later "
        "<https://www.gnu.org/licenses/gpl.html>.\nThis is free "
        "software: you are free to change and redistribute it.\nThere is "
        "[yellow]NO WARRANTY[/yellow], to the extent permitted by law.\n"
        "Written by [underline]ChenPi11[/underline].",
    )

    rich.print(copyright_text)


class _VersionAction(argparse.Action):
    """Version Action for rubisco."""

    def __init__(  # pylint: disable=R0913, R0917
        self,
        option_strings: Sequence[str],
        version: str | None = None,
        dest: str = argparse.SUPPRESS,
        default: str = argparse.SUPPRESS,
        help: str | None = None,  # pylint: disable=W0622 # noqa: A002
    ) -> None:
        if help is None:
            help = _(  # pylint: disable=W0622 # noqa: A001
                "Show program's version number and exit.",
            )
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help,
        )
        self.version = version

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,  # noqa: ARG002
        values: str | Sequence[Any] | None,  # noqa: ARG002
        option_string: str | None = None,  # noqa: ARG002
    ) -> None:
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
    ) -> None:
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

        return help_str.replace("Options:", _("Options:"))


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

arg_parser.add_argument("--root", type=str, help=_("Project root directory."))

arg_parser.add_argument(
    "--log",
    action="store_true",
    help=_("Save log to the log file."),
)

arg_parser.add_argument(
    "--debug",
    action="store_true",
    help=_("Run rubisco in debug mode."),
)

arg_parser.add_argument(
    "--usage",
    action="store_true",
    help=_("Show usage."),
)

arg_parser.add_argument(
    "command",
    action="store",
    nargs="?",
    help=_("Command to run."),
    default=["info"],
)

hook_commands = arg_parser.add_subparsers(
    title=_("Available commands"),
    dest="command",
    metavar="",
    required=False,
)

hook_commands.add_parser(
    "info",
    help=_("Show project information."),
)

project_config: ProjectConfigration | None = None


class RubiscoKTrigger(  # pylint: disable=too-many-public-methods
    IKernelTrigger,
):  # Rubisco CLI kernel trigger.
    """Rubisco kernel trigger."""

    # Singleton pattern, but linter does not like it.
    cur_progress: rich.progress.Progress | None
    tasks: dict[str, rich.progress.TaskID]
    task_types: dict[str, str]
    task_totals: dict[str, float]
    live: rich.live.Live | None
    _speedtest_hosts: dict[str, str]

    def __init__(self) -> None:
        super().__init__()
        self.cur_progress = None
        self.tasks = {}
        self.task_types = {}
        self.task_totals = {}
        self.live = None
        self._speedtest_hosts = {}

    def pre_exec_process(self, proc: Process) -> None:
        output_step(
            format_str(
                _("Executing: [cyan]${{cmd}}[/cyan] ..."),
                fmt={"cmd": proc.origin_cmd.strip()},
            ),
        )
        sys.stdout.write(colorama.Fore.LIGHTBLACK_EX)
        sys.stdout.flush()

    def post_exec_process(
        self,
        proc: Process,  # noqa: ARG002
        retcode: int,  # noqa: ARG002
        raise_exc: bool,  # noqa: ARG002 FBT001
    ) -> None:
        sys.stdout.write(colorama.Fore.RESET)
        sys.stdout.flush()

    def file_exists(self, path: Path) -> None:
        if not ask_yesno(
            format_str(
                _(
                    "File '[underline]${{path}}[/underline]' already exists."
                    " [yellow]Overwrite[/yellow]?",
                ),
                fmt={"path": make_pretty(path.absolute())},
            ),
            default=True,
        ):
            raise KeyboardInterrupt

    def on_new_task(
        self,
        task_name: str,
        task_type: str,
        total: float,
    ) -> None:
        if task_type == IKernelTrigger.TASK_WAIT:
            self.task_types[task_name] = IKernelTrigger.TASK_WAIT
            return

        output_step(task_name)

        if task_type == IKernelTrigger.TASK_DOWNLOAD:
            title = _("[yellow]Downloading[/yellow]")
        elif task_type == IKernelTrigger.TASK_EXTRACT:
            title = _("[yellow]Extracting[/yellow]")
        elif task_type == IKernelTrigger.TASK_COMPRESS:
            title = _("[yellow]Compressing[/yellow]")
        else:
            title = _("[yellow]Processing[/yellow]")

        if self.cur_progress is None:
            self.cur_progress = rich.progress.Progress()
            self.cur_progress.start()
        if task_name in self.tasks:
            self.cur_progress.update(self.tasks[task_name], completed=0)
        task_id = self.cur_progress.add_task(title, total=total)
        self.tasks[task_name] = task_id
        self.task_types[task_name] = task_type
        self.task_totals[task_name] = total

    def on_progress(
        self,
        task_name: str,
        current: float,
        delta: bool = False,  # noqa: FBT001 FBT002
        more_data: dict[str, Any] | None = None,
    ) -> None:
        if more_data is None:
            more_data = {}
        if (
            self.task_types[task_name] == IKernelTrigger.TASK_EXTRACT
            and self.task_totals[task_name] < 2500  # noqa: PLR2004
        ):
            # If extracting a few files (< 2500), show the file name.
            path = str((more_data["dest"] / more_data["path"]).absolute())
            output_line(f"[underline]{path}[/underline]", level=-2)
        elif self.task_types[task_name] == IKernelTrigger.TASK_WAIT:
            output_step(
                format_str(task_name, fmt={"seconds": str(current)}),
                end="\r",
            )
            return
        if self.cur_progress is None:
            logger.warning("Progress not started.")
            return
        if delta:
            self.cur_progress.update(self.tasks[task_name], advance=current)
        else:
            self.cur_progress.update(self.tasks[task_name], completed=current)

    def set_progress_total(self, task_name: str, total: float) -> None:
        if self.cur_progress is None:
            logger.warning("Progress not started.")
            return
        self.cur_progress.update(self.tasks[task_name], total=total)

    def on_finish_task(self, task_name: str) -> None:
        if self.task_types[task_name] == IKernelTrigger.TASK_WAIT:
            del self.task_types[task_name]
            return

        if self.cur_progress is None:
            logger.warning("Progress not started.")
            return
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
                    " [bold]${{packages}}[/bold].",
                ),
                fmt={"packages": ", ".join(packages)},
            ),
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
            ),
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
            ),
        )

    def on_hint(self, message: str) -> None:
        output_hint(message)

    def on_warning(self, message: str) -> None:
        output_warning(message)

    def on_error(self, message: str) -> None:
        output_error(message)

    def _update_live(self) -> None:
        if self.live is None:
            msg = "RubiscoKTrigger.live is None."
            raise ValueError(msg)
        msg = ""
        for host_, status in self._speedtest_hosts.items():
            msg += (
                sum_level_indent(-2)
                + get_prompt(-2, ">", ">")
                + " "
                + format_str(
                    _("Testing ${{host}} ... ${{status}}"),
                    fmt={"host": host_, "status": status},
                )
                + "\n"
            )
        self.live.update(msg)

    def pre_speedtest(self, host: str) -> None:
        if self.live is None:
            output_step(_("Performing websites speed test ..."))
            self.live = rich.live.Live()
            self.live.start()
            self._speedtest_hosts.clear()
        self._speedtest_hosts[host] = _("[yellow]Testing[/yellow] ...")
        self._update_live()

    def post_speedtest(self, host: str, speed: int) -> None:
        if self.live is None:
            msg = "RubiscoKTrigger.live is None."
            raise ValueError(msg)
        if speed == -1:
            self._speedtest_hosts[host] = _("[red]Canceled[/red]")
        elif speed == C_INTMAX:
            self._speedtest_hosts[host] = _("[red]Failed[/red]")
        else:
            self._speedtest_hosts[host] = format_str(
                _("${{speed}} us"),
                fmt={"speed": str(speed)},
            )

        self._update_live()

        cant_stop = False
        for status in self._speedtest_hosts.values():
            cant_stop |= status == _(
                "[yellow]Testing[/yellow] ...",
            )

        if not cant_stop:
            self.live.stop()
            self.live = None

    def stop_speedtest(self, choise: str | None) -> None:
        if self.live is None:
            return
        self.live.stop()
        self.live = None
        if choise:
            output_step(
                format_str(
                    _("Selected mirror: ${{url}}"),
                    fmt={"url": choise},
                ),
            )

    def pre_run_workflow_step(self, step: Step) -> None:
        if step.name.strip():
            output_step(
                format_str(
                    _(  # Don't remove next line's comment.
                        "Running: [white]${{name}}[/white]"  # Black?
                        " [black](${{id}})[/black]",
                    ),
                    fmt={"name": step.name, "id": step.id},
                ),
            )
        push_level()

    def post_run_workflow_step(
        self,
        step: Step,  # noqa: ARG002
    ) -> None:
        pop_level()

    def pre_run_workflow(self, workflow: Workflow) -> None:
        output_step(
            format_str(
                _(
                    "Running workflow: [white]${{name}}[/white] "
                    "[black](${{id}})[/black]",
                ),
                fmt={"name": workflow.name, "id": workflow.id},
            ),
        )
        push_level()

    def post_run_workflow(self, workflow: Workflow) -> None:
        pop_level()
        output_step(
            format_str(
                _("Workflow '${{name}}' finished."),
                fmt={"name": workflow.name},
            ),
        )

    def on_mkdir(self, path: Path) -> None:
        output_step(
            format_str(
                _("Creating directory: [underline]${{path}}[/underline] ..."),
                fmt={"path": make_pretty(path.absolute())},
            ),
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
            ),
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
            ),
        )

    def on_remove(self, path: Path) -> None:
        output_step(
            format_str(
                _("Removing '[underline]${{path}}[/underline]' ..."),
                fmt={"path": make_pretty(path.absolute())},
            ),
        )

    def on_extension_loaded(self, instance: IRUExtention) -> None:
        output_step(
            format_str(
                _("Extension '${{name}}' loaded."),
                fmt={"name": instance.name},
            ),
        )

    def on_show_project_info(self, project: ProjectConfigration) -> None:
        rich.print(
            format_str(
                _(
                    "Rubisco CLI language: '${{locale}}' "
                    "'${{charset}}' '${{language_name}}'",
                ),
                fmt={
                    "locale": locale_language(),
                    "charset": DEFAULT_CHARSET,
                    "language_name": locale_language_name(),
                },
            ),
        )
        rich.print(
            format_str(
                _("[dark_orange]Project:[/dark_orange] ${{name}}"),
                fmt={"name": make_pretty(project.name)},
            ),
        )
        rich.print(
            format_str(
                _(
                    "[dark_orange]Configuration:[/dark_orange] "
                    "[underline]${{path}}[/underline]",
                ),
                fmt={"path": make_pretty(project.config_file)},
            ),
        )
        rich.print(
            format_str(
                _(
                    "[dark_orange]Version:[/dark_orange]"
                    " v[white]${{version}}[/white]",
                ),
                fmt={"version": str(project.version)},
            ),
        )

        if isinstance(project.maintainer, list):
            maintainers = "\n  ".join(project.maintainer)
        else:
            maintainers = str(project.maintainer)
        rich.print(
            format_str(
                _("[dark_orange]Maintainer:[/dark_orange] ${{maintainer}}"),
                fmt={"maintainer": maintainers},
            ),
        )
        rich.print(
            format_str(
                _("[dark_orange]License:[/dark_orange] ${{license}}"),
                fmt={"license": project.license},
            ),
        )
        rich.print(
            format_str(
                _("[dark_orange]Description:[/dark_orange] ${{desc}}"),
                fmt={"desc": project.description},
            ),
        )

        rich.print(_("[dark_orange]Hooks:[/dark_orange]"))

        for hook_name in project.hooks:  # Bind all hooks.
            hook_text = format_str(
                "\t[cyan]${{name}}[/cyan]",
                fmt={"name": hook_name},
            )
            num_text = format_str(
                _("(${{num}} hooks)"),
                fmt={"num": str(len(hooks[hook_name]))},
            )
            formatted_str = f"{hook_text:<60}\t{num_text:<10}"
            rich.print(formatted_str)

    def on_mklink(
        self,
        src: Path,
        dst: Path,
        symlink: bool,  # noqa: FBT001
    ) -> None:
        if symlink:
            output_step(
                format_str(
                    _(
                        "Creating symbolic link: [underline]${{src}}"
                        "[/underline] -> '[underline]${{dst}}[/underline]'...",
                    ),
                    fmt={
                        "src": make_pretty(src.absolute()),
                        "dst": make_pretty(dst.absolute()),
                    },
                ),
            )
        else:
            output_step(
                format_str(
                    _(
                        "Creating hard link: [underline]${{src}}"
                        "[/underline] -> '[underline]${{dst}}[/underline]'...",
                    ),
                    fmt={
                        "src": make_pretty(src.absolute()),
                        "dst": make_pretty(dst.absolute()),
                    },
                ),
            )

    def on_create_venv(self, path: Path) -> None:
        output_step(
            format_str(
                _("Creating venv: '[underline]${{path}}[/underline]' ..."),
                fmt={"path": make_pretty(path.absolute())},
            ),
        )

    def on_install_extension(
        self,
        dest: RUEnvironment,
        ext_name: str,
        ext_version: Version,
    ) -> None:
        if dest.is_global():
            output_step(
                format_str(
                    _(
                        "Installing extension [green]${{name}}[/green]:[cyan]"
                        "${{version}}[/cyan] to global "
                        "([underline]${{path}}[/underline]) ...",
                    ),
                    fmt={
                        "name": ext_name,
                        "version": str(ext_version),
                        "path": make_pretty(dest.path),
                    },
                ),
            )
        elif dest.is_user():
            output_step(
                format_str(
                    _(
                        "Installing extension [green]${{name}}[/green]:[cyan]"
                        "${{version}}[/cyan] to user "
                        "([underline]${{path}}[/underline]) ...",
                    ),
                    fmt={
                        "name": ext_name,
                        "version": str(ext_version),
                        "path": make_pretty(dest.path),
                    },
                ),
            )
        else:
            output_step(
                format_str(
                    _(
                        "Installing extension [green]${{name}}[/green]:[cyan]"
                        "${{version}}[/cyan] to workspace "
                        "([underline]${{path}}[/underline]) ...",
                    ),
                    fmt={
                        "name": ext_name,
                        "version": str(ext_version),
                        "path": make_pretty(dest.path),
                    },
                ),
            )
        push_level()

    def on_extension_installed(
        self,
        dest: Any,  # noqa: ANN401 ARG002
        ext_name: str,
        ext_version: Version,
    ) -> None:
        pop_level()
        output_step(
            format_str(
                _(
                    "Extension [green]${{name}}[/green]:[cyan]${{version}}"
                    "[/cyan] was successfully installed.",
                ),
                fmt={"name": ext_name, "version": str(ext_version)},
            ),
        )


def on_exit() -> None:
    """Reset terminal color."""
    sys.stdout.write(colorama.Fore.RESET)
    sys.stdout.flush()


atexit.register(on_exit)


def bind_hook(name: str) -> None:
    """Bind hook to a command.

    Args:
        name (str): Hook name.

    """
    logger.debug("Binding hook: %s", name)
    if project_config and name in project_config.hooks:
        if name not in hooks:
            hooks[name] = []
        hooks[name].append(project_config.hooks[name])


def call_hook(name: str) -> None:
    """Call a hook.

    Args:
        name (str): The hook name.

    """
    if name not in hooks:
        raise RUValueError(
            format_str(
                _("Undefined command or hook ${{name}}"),
                fmt={"name": make_pretty(name)},
            ),
            hint=_("Perhaps a typo?"),
        )
    for hook in hooks[name]:
        hook.run()


def load_project() -> None:
    """Load the project in cwd."""
    global project_config  # pylint: disable=global-statement # noqa: PLW0603
    try:
        project_config = load_project_config(Path.cwd())
        for hook_name in project_config.hooks:  # Bind all hooks.
            bind_hook(hook_name)
            hook_commands.add_parser(
                hook_name,
                help=format_str(
                    _("(${{num}} hooks)"),
                    fmt={"num": str(len(hooks[hook_name]))},
                ),
            )
    except FileNotFoundError as exc:
        raise RUValueError(
            format_str(
                _(
                    "Working directory '[underline]${{path}}[/underline]'"
                    " not a rubisco project.",
                ),
                fmt={"path": make_pretty(Path.cwd().absolute())},
            ),
            hint=format_str(
                _("'[underline]${{path}}[/underline]' is not found."),
                fmt={"path": make_pretty(USER_REPO_CONFIG.absolute())},
            ),
        ) from exc


def clean_log() -> None:
    """Clean the log file."""
    try:
        line_count = 0
        with Path.open(LOG_FILE, "r+", encoding=DEFAULT_CHARSET) as f:
            for _line in f:
                line_count += 1
                if line_count > DEFAULT_LOG_KEEP_LINES:
                    f.seek(0)
                    f.truncate()
                    return
    except:  # pylint: disable=bare-except  # noqa: E722
        logger.warning("Failed to clean log file.", exc_info=True)

    try:
        line_count = 0
        with Path.open(PIP_LOG_FILE, "r+", encoding=DEFAULT_CHARSET) as f:
            for _line in f:
                line_count += 1
                if line_count > DEFAULT_LOG_KEEP_LINES:
                    f.seek(0)
                    f.truncate()
                    return
    except:  # pylint: disable=bare-except  # noqa: E722 S110
        pass  # Logging a log file exception?


def early_arg_parse() -> None:
    """Parse arguments without argparse.

    Some arguments will be added to argparse later (like hooks).
    If we use argparse here, they will inoperative.
    """
    if "-h" in sys.argv or "--help" in sys.argv:
        arg_parser.print_help()
        sys.exit(0)
    if "-v" in sys.argv or "--version" in sys.argv:
        show_version()
        sys.exit(0)
    if "--usage" in sys.argv:
        arg_parser.print_usage()
        sys.exit(0)
    for idx, arg in enumerate(sys.argv):
        if arg.startswith("--root"):
            if "=" in arg:
                root = arg.split("=")[1].strip()
            else:
                if idx + 1 >= len(sys.argv):
                    arg_parser.print_usage()
                    raise RUError(
                        _("Missing argument for '--root' option."),
                    )
                root = sys.argv[idx + 1].strip()
                if root.startswith("-"):
                    arg_parser.print_usage()
                    raise RUError(
                        _("Missing argument for '--root' option."),
                    )
            if root:
                root = Path(root).absolute()
                output_step(
                    format_str(
                        _("Entering directory '${{path}}'"),
                        fmt={"path": make_pretty(str(root))},
                    ),
                )
                os.chdir(root)


def main() -> None:
    """Rubisco main entry point."""
    try:
        clean_log()
        logger.info("Rubisco CLI version %s started.", str(APP_VERSION))
        colorama.init()
        bind_ktrigger_interface("rubisco", RubiscoKTrigger())
        load_all_extensions()
        early_arg_parse()

        try:
            load_project()
        finally:
            args = arg_parser.parse_args()

        op_command = args.command
        if isinstance(op_command, list):  # This is not a good idea.
            op_command = op_command[0]
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
    except Exception as exc:  # pylint: disable=broad-except # noqa: BLE001
        logger.critical("An unexpected error occurred.", exc_info=True)
        show_exception(exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
