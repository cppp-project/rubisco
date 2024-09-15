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
Package management utils for environment.
"""

import enum
import os
from pathlib import Path
import time
import venv

from rubisco.config import (
    DEFAULT_CHARSET,
    GLOBAL_EXTENSIONS_DIR,
    USER_EXTENSIONS_DIR,
    WORKSPACE_EXTENSIONS_VENV_DIR,
    VENV_LOCK_FILENAME,
)
from rubisco.envutils.utils import is_venv, add_venv_to_syspath
from rubisco.lib.exceptions import RUException, RUOSException
from rubisco.shared.ktrigger import call_ktrigger, IKernelTrigger
from rubisco.lib.variable import format_str
from rubisco.lib.l10n import _
from rubisco.lib.process import is_valid_pid

__all__ = [
    "EnvType",
    "RUEnvironment",
    "setup_new_venv",
    "GLOBAL_ENV",
    "USER_ENV",
    "WORKSPACE_ENV",
]


class EnvType(enum.Enum):
    """Environment type."""

    WORKSPACE = "workspace"
    USER = "user"
    GLOBAL = "global"


class RUEnvironment:
    """Extension environment manager."""

    _path: Path
    _type: EnvType
    _lockfile: Path

    def __init__(self, path: Path, env_type: EnvType) -> None:
        self._path = path
        self._type = env_type
        self._lockfile = self.path / VENV_LOCK_FILENAME

    def _create(self):
        if not is_venv(self.path):
            setup_new_venv(self)

    @property
    def path(self) -> Path:
        """Get the path of the environment."""

        return self._path

    @property
    def type(self) -> EnvType:
        """Get the type of the environment."""

        return self._type

    def is_global(self) -> bool:
        """Check if the environment is global."""

        return self.type == EnvType.GLOBAL

    def is_user(self) -> bool:
        """Check if the environment is user."""

        return self.type == EnvType.USER

    def is_workspace(self) -> bool:
        """Check if the environment is workspace."""

        return self.type == EnvType.WORKSPACE

    def is_locked(self) -> bool:
        """Check if the environment is locked."""

        return self._lockfile.exists()

    def lock(self) -> None:
        """Lock the environment."""

        self._create()

        if self.is_locked():
            pid = -1
            try:
                with open(self._lockfile, encoding=DEFAULT_CHARSET) as f:
                    pid = int(f.read().strip())
            except ValueError:
                pass

            call_ktrigger(
                IKernelTrigger.on_warning,
                message=format_str(
                    _(
                        "The environment '${{path}}' is already locked by PID "
                        "${{pid}}. If you want to force unlock it, please "
                        "remove the lock file '${{lockfile}}' manually."
                    ),
                    fmt={
                        "path": self.path,
                        "pid": _("Unknown") if pid == -1 else pid,
                        "lockfile": self._lockfile,
                    },
                ),
            )
            if pid != -1 and not is_valid_pid(pid):
                call_ktrigger(
                    IKernelTrigger.on_warning,
                    message=format_str(
                        _(
                            "The PID '${{pid}}' is not valid. Maybe the "
                            "process has already exited. Remove the lock file "
                            "if you believe the process has already exited."
                        ),
                        fmt={
                            "pid": str(pid),
                        },
                    ),
                )

            task_name = format_str(
                _(
                    "Waiting for the environment to be unlocked "
                    "('${{lock_file}}'): ${{seconds}} seconds.",
                ),
                fmt={
                    "lock_file": self._lockfile,
                },
            )
            call_ktrigger(
                IKernelTrigger.on_new_task,
                task_name=task_name,
                task_type=IKernelTrigger.TASK_WAIT,
                total=0,
            )
            wait_time = 0
            while self.is_locked():
                call_ktrigger(
                    IKernelTrigger.on_progress,
                    task_name=task_name,
                    current=wait_time,
                    delta=False,
                    more_data={"env": self},
                )
                time.sleep(1)
                wait_time += 1

            call_ktrigger(
                IKernelTrigger.on_finish_task,
                task_name=task_name,
            )

        pid = os.getpid()
        with open(
            self.path / VENV_LOCK_FILENAME,
            "w",
            encoding=DEFAULT_CHARSET,
        ) as f:
            f.write(str(pid))

    def unlock(self) -> None:
        """Unlock the environment."""

        if self.is_locked():
            os.remove(self.path / VENV_LOCK_FILENAME)

    def __enter__(self) -> "RUEnvironment":
        self.lock()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.unlock()

    def add_to_path(self) -> None:
        """Add the environment to the system path."""

        add_venv_to_syspath(self.path)


def setup_new_venv(env: RUEnvironment) -> None:
    """Setup a new Python virtual environment for Rubisco extensions.

    Args:
        env (RUEnvironment): Path to setup the virtual environment.
    """

    call_ktrigger(IKernelTrigger.on_create_venv, path=env.path)
    try:
        if env.path.exists() and not is_venv(env.path):
            raise RUException(
                hint=format_str(
                    _(
                        "The '${{path}}' is not a valid venv but exists."
                        "Please remove it and try again."
                    ),
                    fmt={"path": env.path},
                )
            )
        venv.create(env.path, with_pip=True, upgrade_deps=True)
        add_venv_to_syspath(env.path)
    except OSError as exc:
        raise RUOSException(
            exc,
            hint=_(
                "Failed to create venv. Consider to check the"
                "permissions of the path."
            ),
        ) from exc


GLOBAL_ENV = RUEnvironment(GLOBAL_EXTENSIONS_DIR, EnvType.GLOBAL)
USER_ENV = RUEnvironment(USER_EXTENSIONS_DIR, EnvType.USER)
WORKSPACE_ENV = RUEnvironment(WORKSPACE_EXTENSIONS_VENV_DIR, EnvType.WORKSPACE)

GLOBAL_ENV.add_to_path()
USER_ENV.add_to_path()
WORKSPACE_ENV.add_to_path()
