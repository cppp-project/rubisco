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
Repoutils kernel trigger.
Kernel trigger is called when kernel do something. It makes User Control
Interface can do something before or after kernel operations.
"""

from functools import partial
from pathlib import Path
from typing import Any, Callable

from repoutils.lib.exceptions import RUValueException
from repoutils.lib.l10n import _
from repoutils.lib.log import logger
from repoutils.lib.variable import format_str

__all__ = [
    "IKernelTrigger",
    "bind_ktrigger_interface",
    "call_ktrigger",
]


def _null_trigger(name, *args, **kwargs) -> None:
    logger.debug(
        "Not implemented KTrigger '%s' called(%s, %s).",
        name,
        repr(args),
        repr(kwargs),
    )


class IKernelTrigger:
    """
    Kernel trigger interface.
    """

    TASK_DOWNLOAD = "download"
    TASK_EXTRACT = "extract"

    def pre_exec_process(self, proc: Any) -> None:
        """Pre-exec process.

        Args:
            proc (Process): Process instance.
        """

        _null_trigger("pre_exec_process", proc=proc)

    def post_exec_process(
        self,
        proc: Any,
        retcode: int,
        raise_exc: bool,
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

    def file_exists(self, path: str) -> None:
        """Ask user to overwrite a file.

        Args:
            path (str): File path.
        """

        _null_trigger("file_exists", path=path)

    def on_new_task(
        self,
        task_name: str,
        task_type: int,
        total: int | float,
    ) -> None:
        """When a progressive task is created.

        Args:
            task_name (str): Task name.
            task_type (int): Task type.
            total (int | float): Total steps.
        """

        _null_trigger(
            "on_progressive_task",
            task_name=task_name,
            task_type=task_type,
            total=total,
        )

    def on_progress(
        self,
        task_name: str,
        current: int | float,
        delta: bool = False,
    ):
        """When the progressive task progress is updated.

        Args:
            task_name (str): Task name.
            current (int | float): Current step.
            delta (bool): If the current is delta.
        """

        _null_trigger(
            "on_progress",
            task_name=task_name,
            current=current,
            delta=delta,
        )

    def set_progress_total(self, task_name: str, total: int | float):
        """Set the total steps of a progressive task.

        Args:
            task_name (str): Task name.
            total (int | float): Total steps.
        """

        _null_trigger(
            "set_progress_total",
            task_name=task_name,
            total=total,
        )

    def on_finish_task(self, task_name: str):
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

    def on_update_git_repo(
        self,
        path: Path,
        branch: str,
    ) -> None:
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
                -1 means canceled, C_INTMAX means failed.
        """

        _null_trigger("post_speedtest", host=host, speed=speed)

    def pre_run_workflow_step(self, step: Any) -> None:
        """When a workflow is started.

        Args:
            step (Step): The step.
        """

        _null_trigger("pre_run_workflow_step", step=step)

    def post_run_workflow_step(self, step: Any) -> None:
        """When a workflow is finished.

        Args:
            step (Step): The step.
        """

        _null_trigger("post_run_workflow_step", step=step)

    def pre_run_workflow(self, workflow: Any) -> None:
        """When a workflow is started.

        Args:
            workflow (Workflow): The workflow.
        """

        _null_trigger("pre_run_workflow", workflow=workflow)

    def post_run_workflow(self, workflow: Any) -> None:
        """When a workflow is finished.

        Args:
            workflow (Workflow): The workflow.
        """

        _null_trigger("post_run_workflow", workflow=workflow)


# KTrigger instances.
ktriggers: dict[str, IKernelTrigger] = {}


def bind_ktrigger_interface(sign: str, instance: IKernelTrigger) -> None:
    """Bind a KTrigger instance with a sign.

    Args:
        sign (str): KTrigger's sign. It MUST be unique.
        instance (IKernelTrigger): KTrigger instance.

    Raises:
        RUValueException: If sign is already exists.
        TypeError: If instance is not a IKernelTrigger instance.
    """

    if not isinstance(instance, IKernelTrigger):
        raise TypeError(
            format_str(
                _("'{name}' is not a IKernelTrigger instance."),
                fmt={"name": repr(instance)},
            )
        )

    if sign in ktriggers:
        raise RUValueException(
            format_str(
                _("Kernel trigger sign '{name}' is already exists."),
                fmt={"name": str(sign)},
            )
        )

    ktriggers[sign] = instance
    logger.debug("Bind kernel trigger '%s' to '%s'.", sign, repr(instance))


def call_ktrigger(name: str | Callable, *args, **kwargs) -> None:
    """Call a KTrigger.

    Args:
        name (str | Callable): KTrigger's name.

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
    import rich

    rich.print(f"{__file__}: {__doc__.strip()}")

    # Test: Bind a KTrigger.
    class _TestKTrigger(IKernelTrigger):
        _prog_total: int | float
        _prog_current: int | float

        def on_test0(self) -> None:
            "Test0: KTrigger without arguments."

            rich.print("on_test0()")

        def on_test1(self, arg1: str, arg2: str) -> None:
            "Test1: KTrigger with two arguments."
            rich.print("on_test1():", arg1, arg2)
            assert arg1 == "Linus"
            assert arg2 == "Torvalds"

        def on_test2(self, *args, **kwargs) -> None:
            "Test2: KTrigger with *args and **kwargs."
            rich.print("on_test2():", args, kwargs)
            assert args == ("Linus", "Torvalds")
            assert kwargs == {"gnu": "Stallman", "nividia": "F**k"}

        def on_test3(self) -> None:
            "Test3: KTrigger raises an exception."
            raise ValueError("Test3 exception.")

    kt = _TestKTrigger()
    bind_ktrigger_interface("test", kt)

    # Test: Bind a KTrigger with the same sign.
    try:
        bind_ktrigger_interface("test", kt)
    except RUValueException:
        pass

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
    try:
        call_ktrigger("on_test3")
    except ValueError:
        pass

    # Test: Call a non-exists KTrigger.
    call_ktrigger("non_exists")
