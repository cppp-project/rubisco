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

    def on_finish_task(self, task_name: str):
        """When a progressive task is finished.

        Args:
            task_name (str): Task name.
        """

        _null_trigger("on_finish_task", task_name=task_name)


# KTrigger instances.
ktriggers: dict[str, IKernelTrigger] = {}


def bind_ktrigger_interface(sign: str, instance: IKernelTrigger) -> None:
    """Bind a KTrigger instance with a sign.

    Args:
        sign (str): KTrigger's sign. It MUST be unique.
        instance (IKernelTrigger): KTrigger instance.

    Raises:
        RUValueException: If sign is already exists.
    """

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
        name (str | Callable): KTrigger's name. If it's a Callable, it will
            be converted to its name. (Using callable can avoid typo.)

    Hint:
        Passing arguments by kwargs is recommended. It can make the code
        more readable.
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
    print(f"{__file__}: {__doc__.strip()}")

    import time

    # Test: Bind a KTrigger.
    class _TestKTrigger(IKernelTrigger):
        _prog_total: int | float
        _prog_current: int | float

        def on_test0(self) -> None:
            "Test0: KTrigger without arguments."

            print("on_test0()")

        def on_test1(self, arg1: str, arg2: str) -> None:
            "Test1: KTrigger with two arguments."
            print("on_test1():", arg1, arg2)
            assert arg1 == "Linus"
            assert arg2 == "Torvalds"

        def on_test2(self, *args, **kwargs) -> None:
            "Test2: KTrigger with *args and **kwargs."
            print("on_test2():", args, kwargs)
            assert args == ("Linus", "Torvalds")
            assert kwargs == {"gnu": "Stallman", "nividia": "F**k"}

        def on_test3(self) -> None:
            "Test3: KTrigger raises an exception."
            raise ValueError("Test3 exception.")

        def on_new_task(
            self, task_name: str, task_type: int, total: int | float
        ) -> None:
            print("on_new_task():", task_name, task_type, total)
            self._prog_total = total
            self._prog_current = 0

        def on_progress(
            self,
            task_name: str,
            current: int | float,
            delta: bool = False,
        ):
            if delta:
                self._prog_current += current
            else:
                self._prog_current = current
            print(
                "on_progress():",
                task_name,
                self._prog_current,
                "/",
                self._prog_total,
                end="\r",
            )

        def on_finish_task(self, task_name: str):
            print("on_finish_task():", task_name)

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

    # Test: Progressive task.
    call_ktrigger(
        "on_new_task",
        task_name="TestTask",
        task_type=IKernelTrigger.TASK_DOWNLOAD,
        total=100,
    )
    for i in range(101):
        call_ktrigger("on_progress", task_name="TestTask", current=i)
        time.sleep(0.01)
    print()
    call_ktrigger("on_finish_task", task_name="TestTask")
