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

"""Rubisco kernel trigger.

Kernel trigger is called when kernel do something. It makes User Control
Interface can do something before or after kernel operations.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING, Any

from rubisco.lib.exceptions import RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.variable import format_str, make_pretty

if TYPE_CHECKING:
    from rubisco.lib.pathlib import Path
    from rubisco.lib.version import Version

__all__ = [
    "IKernelTrigger",
    "bind_ktrigger_interface",
    "call_ktrigger",
]


def _null_trigger(
    name: str,
    *args: Any,  # noqa: ANN401
    **kwargs: Any,  # noqa: ANN401
) -> None:
    logger.debug(
        "Not implemented KTrigger '%s' called(%s, %s).",
        name,
        repr(args),
        repr(kwargs),
    )


class IKernelTrigger:  # pylint: disable=too-many-public-methods
    """Kernel trigger interface."""

    TASK_DOWNLOAD = "download"
    TASK_EXTRACT = "extract"
    TASK_COMPRESS = "compress"
    TASK_WAIT = "wait"

    def pre_exec_process(self, proc: Any) -> None:  # noqa: ANN401
        """Pre-exec process.

        Args:
            proc (Process): Process instance.

        """
        _null_trigger("pre_exec_process", proc=proc)

    def post_exec_process(
        self,
        proc: Any,  # noqa: ANN401
        retcode: int,
        raise_exc: bool,  # noqa: FBT001
    ) -> None:
        """Post-exec process.

        Args:
            proc (Process): Process instance.
            retcode (int): Return code.
            raise_exc (bool): If raise exception.

        """
        _null_trigger(
            "post_exec_process",
            proc=proc,
            retcode=retcode,
            raise_exc=raise_exc,
        )

    def file_exists(self, path: Path) -> None:
        """Ask user to overwrite a file.

        Args:
            path (Path): File path.

        """
        _null_trigger("file_exists", path=path)

    def on_new_task(
        self,
        task_name: str,
        task_type: str,
        total: float,
    ) -> None:
        """When a progressive task is created.

        Args:
            task_name (str): Task name.
            task_type (str): Task type.
                Must be `IKernelTrigger.TASK_*`.
            total (float): Total steps.

        """
        _null_trigger(
            "on_new_task",
            task_name=task_name,
            task_type=task_type,
            total=total,
        )

    def on_progress(
        self,
        task_name: str,
        current: float,
        delta: bool = False,  # noqa: FBT001 FBT002
        more_data: dict[str, Any] | None = None,
    ) -> None:
        """When the progressive task progress is updated.

        Args:
            task_name (str): Task name.
            current (int | float): Current step.
            delta (bool): If the current is delta.
            more_data (dict[str, Any] | None): More data of the progress.

        """
        _null_trigger(
            "on_progress",
            task_name=task_name,
            current=current,
            delta=delta,
            more_data=more_data,
        )

    def set_progress_total(self, task_name: str, total: float) -> None:
        """Set the total steps of a progressive task.

        Args:
            task_name (str): Task name.
            total (float): Total steps.

        """
        _null_trigger(
            "set_progress_total",
            task_name=task_name,
            total=total,
        )

    def on_finish_task(self, task_name: str) -> None:
        """When a progressive task is finished.

        Args:
            task_name (str): Task name.

        """
        _null_trigger("on_finish_task", task_name=task_name)

    def on_syspkg_installation_skip(
        self,
        packages: list[str],
        message: str,
    ) -> None:
        """When a system package installation is skipped.

        Args:
            packages (list[str]): Package name.
            message (str): Skip reason.

        """
        _null_trigger(
            "on_syspkg_installation_skip",
            packages=packages,
            message=message,
        )

    def on_update_git_repo(self, path: Path, branch: str) -> None:
        """When a git repository is updating.

        Args:
            path (Path): Repository path.
            branch (str): Branch name.

        """
        _null_trigger(
            "on_update_git_repo",
            path=path,
            branch=branch,
        )

    def on_clone_git_repo(
        self,
        url: str,
        path: Path,
        branch: str,
    ) -> None:
        """When a git repository is cloning.

        Args:
            url (str): Repository URL.
            path (Path): Repository path.
            branch (str): Branch name.

        """
        _null_trigger(
            "on_clone_git_repo",
            url=url,
            path=path,
            branch=branch,
        )

    def on_hint(self, message: str) -> None:
        """When a hint is got.

        Args:
            message (str): Hint message.

        """
        _null_trigger("on_hint", message=message)

    def on_warning(self, message: str) -> None:
        """When a warning is raised.

        Args:
            message (str): Warning message.

        """
        _null_trigger("on_warning", message=message)

    def on_error(self, message: str) -> None:
        """When a error is raised.

        Args:
            message (str): Error message.

        """
        _null_trigger("on_error", message=message)

    def pre_speedtest(self, host: str) -> None:
        """When a speed test task is started.

        Args:
            host (str): Host to test.

        """
        _null_trigger("pre_speedtest", host=host)

    def post_speedtest(self, host: str, speed: int) -> None:
        """When a speed test task is finished.

        Args:
            host (str): Host to test.
            speed (int): Speed of the host. (us)
                `-1` means canceled, `C_INTMAX` means failed.

        """
        _null_trigger("post_speedtest", host=host, speed=speed)

    def stop_speedtest(self, choise: str | None) -> None:
        """When a speed test task is stopped.

        Args:
            choise (str | None): User's choise. None means error.

        """
        _null_trigger("stop_speedtest", choise=choise)

    def pre_run_workflow_step(self, step: Any) -> None:  # noqa: ANN401
        """When a workflow is started.

        Args:
            step (Step): The step.

        """
        _null_trigger("pre_run_workflow_step", step=step)

    def post_run_workflow_step(self, step: Any) -> None:  # noqa: ANN401
        """When a workflow is finished.

        Args:
            step (Step): The step.

        """
        _null_trigger("post_run_workflow_step", step=step)

    def pre_run_workflow(self, workflow: Any) -> None:  # noqa: ANN401
        """When a workflow is started.

        Args:
            workflow (Workflow): The workflow.

        """
        _null_trigger("pre_run_workflow", workflow=workflow)

    def post_run_workflow(self, workflow: Any) -> None:  # noqa: ANN401
        """When a workflow is finished.

        Args:
            workflow (Workflow): The workflow.

        """
        _null_trigger("post_run_workflow", workflow=workflow)

    def on_mkdir(self, path: Path) -> None:
        """On we are creating directories.

        Args:
            path (Path): Directory/directories's path.

        """
        _null_trigger("on_mkdir", path=path)

    def on_output(self, msg: str) -> None:
        """Output a message.

        Args:
            msg (str): Message.

        """
        _null_trigger("on_output", msg=msg)

    def on_move_file(self, src: Path, dst: Path) -> None:
        """On we are moving files.

        Args:
            src (Path): Source file path.
            dst (Path): Destination file path.

        """
        _null_trigger("on_move_file", src=src, dst=dst)

    def on_copy(self, src: Path, dst: Path) -> None:
        """On we are copying files.

        Args:
            src (Path): Source file path.
            dst (Path): Destination file path.

        """
        _null_trigger("on_copy", src=src, dst=dst)

    def on_remove(self, path: Path) -> None:
        """On we are removing files.

        Args:
            path (Path): File path.

        """
        _null_trigger("on_remove", path=path)

    def on_extension_loaded(self, instance: Any) -> None:  # noqa: ANN401
        """On a extension loaded.

        Args:
            instance (IRUExtention): Extention instance.

        """
        _null_trigger("on_extension_loaded", instance=instance)

    def on_show_project_info(self, project: Any) -> None:  # noqa: ANN401
        """On show project information.

        Args:
            project (ProjectConfigration): Project configuration.

        """
        _null_trigger("on_show_project_info", project=project)

    def on_mklink(
        self,
        src: Path,
        dst: Path,
        symlink: bool,  # noqa: FBT001
    ) -> None:
        """On we are creating a symlink.

        Args:
            src (Path): Source file path.
            dst (Path): Destination file path.
            symlink (bool): If it is a symlink.

        """
        _null_trigger("on_mklink", src=src, dst=dst, symlink=symlink)

    def on_create_venv(self, path: Path) -> None:
        """On we are creating a virtual environment.

        Args:
            path (Path): Virtual environment path.

        """
        _null_trigger("on_create_venv", path=path)

    def on_install_extension(
        self,
        dest: Any,  # noqa: ANN401
        ext_name: str,
        ext_version: Version,
    ) -> None:
        """On we are installing an extension.

        Args:
            dest (RUEnvironment): Destination environment.
            ext_name (str): Extension name.
            ext_version (Version): Extension version.

        """
        _null_trigger(
            "on_install_extension",
            dest=dest,
            ext_name=ext_name,
            ext_version=ext_version,
        )

    def on_extension_installed(
        self,
        dest: Any,  # noqa: ANN401
        ext_name: str,
        ext_version: Version,
    ) -> None:
        """On a extension installed.

        Args:
            dest (RUEnvironment): Destination environment type.
            ext_name (str): Extension name.
            ext_version (Version): Extension version.

        """
        _null_trigger(
            "on_extension_installed",
            dest=dest,
            ext_name=ext_name,
            ext_version=ext_version,
        )

    def on_uninstall_extension(
        self,
        dest: Any,  # noqa: ANN401
        ext_name: str,
        ext_version: Version,
    ) -> None:
        """On we are removing an extension.

        Args:
            dest (RUEnvironment): Destination environment type.
            ext_name (str): Extension name.
            ext_version (Version): Extension version.

        """
        _null_trigger(
            "on_uninstall_extension",
            dest=dest,
            ext_name=ext_name,
            ext_version=ext_version,
        )

    def on_extension_uninstalled(
        self,
        dest: Any,  # noqa: ANN401
        ext_name: str,
        ext_version: Version,
    ) -> None:
        """On a extension removed.

        Args:
            dest (RUEnvironment): Destination environment type.
            ext_name (str): Extension name.
            ext_version (Version): Extension version.

        """
        _null_trigger(
            "on_extension_uninstalled",
            dest=dest,
            ext_name=ext_name,
            ext_version=ext_version,
        )

    def on_upgrade_extension(
        self,
        dest: Any,  # noqa: ANN401
        ext_name: str,
        ext_version: Version,
    ) -> None:
        """On we are upgrading an extension.

        Args:
            dest (RUEnvironment): Destination environment type.
            ext_name (str): Extension name.
            ext_version (Version): Extension version.

        """
        _null_trigger(
            "on_upgrade_extension",
            dest=dest,
            ext_name=ext_name,
            ext_version=ext_version,
        )

    def on_extension_upgraded(
        self,
        dest: Any,  # noqa: ANN401
        ext_name: str,
        ext_version: Version,
    ) -> None:
        """On a extension upgraded.

        Args:
            dest (RUEnvironment): Destination environment type.
            ext_name (str): Extension name.
            ext_version (Version): Extension version.

        """
        _null_trigger(
            "on_extension_upgraded",
            dest=dest,
            ext_name=ext_name,
            ext_version=ext_version,
        )


# KTrigger instances.
ktriggers: dict[str, IKernelTrigger] = {}


def bind_ktrigger_interface(kid: str, instance: IKernelTrigger) -> None:
    """Bind a KTrigger instance with a id.

    Args:
        kid (str): KTrigger's id. It MUST be unique.
        instance (IKernelTrigger): KTrigger instance.

    Raises:
        RUValueError: If id is already exists.
        TypeError: If instance is not a IKernelTrigger instance.

    """
    if not isinstance(instance, IKernelTrigger):
        raise TypeError(
            format_str(
                _("'${{name}}' is not a IKernelTrigger instance."),
                fmt={"name": make_pretty(instance)},
            ),
        )

    if kid in ktriggers:
        raise RUValueError(
            format_str(
                _("Kernel trigger id '${{name}}' is already exists."),
                fmt={"name": make_pretty(kid)},
            ),
        )

    ktriggers[kid] = instance
    logger.debug("Bind kernel trigger '%s' to '%s'.", kid, repr(instance))


def call_ktrigger(
    name: str | Callable,
    *args: Any,  # noqa: ANN401
    **kwargs: Any,  # noqa: ANN401
) -> None:
    """Call a KTrigger.

    Args:
        name (str | Callable): KTrigger's name.
        *args (Any): Arguments.
        **kwargs (Any): Keyword arguments

    Hint:
        Passing arguments by kwargs is recommended. It can make the code
        more readable and avoid bug caused by the wrong order of arguments.

    """
    if isinstance(name, Callable):
        name = name.__name__
    logger.debug(
        "Calling kernel trigger '%s'(%s, %s). %s",
        name,
        repr(args),
        repr(kwargs),
        repr(list(ktriggers.keys())),
    )
    for instance in ktriggers.values():
        getattr(instance, name, partial(_null_trigger, name))(*args, **kwargs)


if __name__ == "__main__":
    from contextlib import suppress

    import rich

    # Test: Bind a KTrigger.
    class _TestKTrigger(IKernelTrigger):
        _prog_total: int | float
        _prog_current: int | float

        def on_test0(self) -> None:
            """Test0: KTrigger without arguments."""
            rich.print("on_test0()")

        def on_test1(self, arg1: str, arg2: str) -> None:
            """Test1: KTrigger with two arguments."""
            rich.print("on_test1():", arg1, arg2)
            assert arg1 == "Linus"  # noqa: S101
            assert arg2 == "Torvalds"  # noqa: S101

        def on_test2(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
            """Test2: KTrigger with *args and **kwargs."""
            rich.print("on_test2():", args, kwargs)
            assert args == ("Linus", "Torvalds")  # noqa: S101
            assert kwargs == {  # noqa: S101
                "gnu": "Stallman",
                "nividia": "F**k",
            }

        def on_test3(self) -> None:
            """Test3: KTrigger raises an exception."""
            msg = "Test3 exception."
            raise ValueError(msg)

    kt = _TestKTrigger()
    bind_ktrigger_interface("test", kt)

    # Test: Bind a KTrigger with the same sign.
    with suppress(RUValueError):
        bind_ktrigger_interface("test", kt)

    # Test: Call a KTrigger.
    call_ktrigger("on_test0")
    call_ktrigger("on_test1", "Linus", "Torvalds")
    call_ktrigger(
        "on_test2",
        "Linus",
        "Torvalds",
        gnu="Stallman",
        nividia="F**k",
    )
    with suppress(ValueError):
        call_ktrigger("on_test3")

    # Test: Call a non-exists KTrigger.
    call_ktrigger("non_exists")


# Death is a form of liberation.
# RIGHT. But I don't want to be liberated.
