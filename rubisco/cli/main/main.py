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

import atexit
import sys

import colorama

from rubisco.cli.main.arg_parser import arg_parser, early_arg_parse
from rubisco.cli.main.ktrigger import RubiscoKTrigger
from rubisco.cli.main.log_cleaner import clean_log
from rubisco.cli.main.project_config import (
    call_hook,
    get_project_config,
    load_project,
)
from rubisco.cli.output import show_exception
from rubisco.config import (
    APP_VERSION,
)
from rubisco.lib.log import logger
from rubisco.shared.extension import load_all_extensions
from rubisco.shared.ktrigger import (
    IKernelTrigger,
    bind_ktrigger_interface,
    call_ktrigger,
)

__all__ = ["main"]


def on_exit() -> None:
    """Reset terminal color."""
    sys.stdout.write(colorama.Fore.RESET)
    sys.stdout.flush()


atexit.register(on_exit)


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
                project=get_project_config(),
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
