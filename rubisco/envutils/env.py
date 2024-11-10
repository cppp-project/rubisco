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

"""Package management utils for environment."""

import enum
import os
import sqlite3
import sys
import time
import venv
from pathlib import Path

from rubisco.config import (
    DB_FILENAME,
    DEFAULT_CHARSET,
    EXTENSIONS_DIR,
    GLOBAL_EXTENSIONS_VENV_DIR,
    USER_EXTENSIONS_VENV_DIR,
    VENV_LOCK_FILENAME,
    WORKSPACE_EXTENSIONS_VENV_DIR,
)
from rubisco.envutils.utils import add_venv_to_syspath, is_venv
from rubisco.lib.exceptions import RUError, RUOSError
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.process import is_valid_pid
from rubisco.lib.variable import format_str, make_pretty
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

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
    db_file: Path

    def __init__(self, path: Path, env_type: EnvType) -> None:
        """Initialize the environment manager."""
        self._path = path
        self._type = env_type
        self._lockfile = self.path / VENV_LOCK_FILENAME
        self.db_file = self.path / DB_FILENAME

    def _create(self) -> None:
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
                with Path.open(self._lockfile, encoding=DEFAULT_CHARSET) as f:
                    pid = int(f.read().strip())
            except ValueError:
                pass

            logger.warning(
                "The environment '%s' is already locked by PID %d. "
                "If you want to force unlock it, please remove the "
                "lock file '%s' manually.",
                self.path,
                pid,
                self._lockfile,
            )
            call_ktrigger(
                IKernelTrigger.on_warning,
                message=format_str(
                    _(
                        "The environment '${{path}}' is already locked by PID "
                        "${{pid}}. If you want to force unlock it, please "
                        "remove the lock file '${{lockfile}}' manually.",
                    ),
                    fmt={
                        "path": str(self.path),
                        "pid": str(_("Unknown") if pid == -1 else pid),
                        "lockfile": str(self._lockfile),
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
                            "if you believe the process has already exited.",
                        ),
                        fmt={
                            "pid": str(pid),
                        },
                    ),
                )

            logger.info(
                "Waiting for the environment to be unlocked ('%s')",
                self._lockfile,
            )

            task_name = format_str(
                _(
                    "Waiting for the environment to be unlocked "
                    "('${{lock_file}}'): ${{seconds}} seconds.",
                ),
                fmt={
                    "lock_file": str(self._lockfile),
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
        logger.info(
            "Locking the environment '%s' with PID %d.",
            self.path,
            pid,
        )
        with Path.open(
            self.path / VENV_LOCK_FILENAME,
            "w",
            encoding=DEFAULT_CHARSET,
        ) as f:
            f.write(str(pid))

    def unlock(self) -> None:
        """Unlock the environment."""
        if self.is_locked():
            logger.info("Unlocking the environment '%s'.", self.path)
            # Missing is OK but not OK.
            Path.unlink(self.path / VENV_LOCK_FILENAME, missing_ok=True)
        else:
            logger.warning("The environment '%s' is not locked.", self.path)

    def __enter__(self) -> "RUEnvironment":
        """Lock the environment."""
        self.lock()
        return self

    def __exit__(
        self,
        exc_type,  # noqa: ANN001
        exc_value,  # noqa: ANN001
        traceback,  # noqa: ANN001
    ) -> None:
        """Unlock the environment."""
        self.unlock()

    def add_to_path(self) -> None:
        """Add the environment to the system path."""
        add_venv_to_syspath(self.path)


def setup_new_venv(env: RUEnvironment) -> None:
    """Set up a new Python virtual environment for Rubisco extensions.

    Args:
        env (RUEnvironment): Path to setup the virtual environment.

    """
    logger.info("Setting up a new venv: '%s'", env.path)
    call_ktrigger(IKernelTrigger.on_create_venv, path=env.path)
    try:
        if env.path.exists() and not is_venv(env.path):
            raise RUError(
                hint=format_str(
                    _(
                        "The '${{path}}' is not a valid venv but exists."
                        "Please remove it and try again.",
                    ),
                    fmt={"path": str(env.path)},
                ),
            )
        venv.create(env.path, with_pip=True, upgrade_deps=True)
        (env.path / EXTENSIONS_DIR).mkdir(exist_ok=True, parents=True)
        logger.debug("Creating database %s", env.db_file)
        db_connection = sqlite3.connect(env.db_file)
        db_cursor = db_connection.cursor()
        db_cursor.execute(
            """
CREATE TABLE extensions (
    name VARCHAR() PRIMARY KEY,
    version VARCHAR(64) NOT NULL,
    description TEXT,
    homepage TEXT,
    maintainers TEXT,
    license TEXT,
    tags TEXT,
    requirements TEXT
)
            """,
        )
        db_connection.commit()
        db_connection.close()
        add_venv_to_syspath(env.path)
    except OSError as exc:
        raise RUOSError(
            exc,
            hint=_(
                "Failed to create venv. Consider to check the"
                "permissions of the path.",
            ),
        ) from exc
    except sqlite3.Error as exc:
        raise RUError(
            exc,
            hint=_(
                "Failed to create the database for the environment.",
            ),
        ) from exc


GLOBAL_ENV = RUEnvironment(GLOBAL_EXTENSIONS_VENV_DIR, EnvType.GLOBAL)
USER_ENV = RUEnvironment(USER_EXTENSIONS_VENV_DIR, EnvType.USER)
WORKSPACE_ENV = RUEnvironment(WORKSPACE_EXTENSIONS_VENV_DIR, EnvType.WORKSPACE)

GLOBAL_ENV.add_to_path()
USER_ENV.add_to_path()
WORKSPACE_ENV.add_to_path()


if __name__ == "__main__":
    import rubisco.cli.output
    import rubisco.shared.ktrigger

    class _InstallTrigger(IKernelTrigger):
        def on_create_venv(self, path: Path) -> None:
            rubisco.cli.output.output_step(
                format_str(
                    _("Creating venv: '[underline]${{path}}[/underline]' ..."),
                    fmt={"path": make_pretty(path.absolute())},
                ),
            )

    rubisco.shared.ktrigger.bind_ktrigger_interface(
        "installer",
        _InstallTrigger(),
    )

    if "--setup-global-env" in sys.argv:
        try:
            setup_new_venv(GLOBAL_ENV)
        except (
            Exception  # pylint: disable=broad-exception-caught  # noqa: BLE001
        ) as exc_:
            logger.exception("Failed to setup global environment.")
            rubisco.cli.output.show_exception(exc_)
    elif "--setup-user-env" in sys.argv:
        try:
            setup_new_venv(USER_ENV)
        except (
            Exception  # pylint: disable=broad-exception-caught  # noqa: BLE001
        ) as exc_:
            logger.exception("Failed to setup user environment.")
            rubisco.cli.output.show_exception(exc_)
    elif "--setup-workspace-env" in sys.argv:
        try:
            setup_new_venv(WORKSPACE_ENV)
        except (
            Exception  # pylint: disable=broad-exception-caught  # noqa: BLE001
        ) as exc_:
            logger.exception("Failed to setup workspace environment.")
            rubisco.cli.output.show_exception(exc_)
