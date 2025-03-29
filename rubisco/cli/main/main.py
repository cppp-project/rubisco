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
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import colorama

from rubisco.cli.main.arg_parser import arg_parser
from rubisco.cli.main.builtin_cmds import register_builtin_cmds
from rubisco.cli.main.extman_cmds import register_extman_cmds
from rubisco.cli.main.ktrigger import RubiscoKTrigger
from rubisco.cli.main.log_cleaner import clean_logfile
from rubisco.cli.main.project_config import get_project_config, load_project
from rubisco.cli.output import output_step, set_available_color, show_exception
from rubisco.config import (
    APP_VERSION,
)
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.variable import format_str, make_pretty
from rubisco.shared.extension import load_all_extensions
from rubisco.shared.ktrigger import (
    bind_ktrigger_interface,
)

if TYPE_CHECKING:
    import argparse

__all__ = ["main"]


def on_exit() -> None:
    """Reset terminal color."""
    sys.stdout.write(colorama.Fore.RESET)
    sys.stdout.flush()


atexit.register(on_exit)


def parse_root_argument(args: argparse.Namespace) -> None:
    """Parse '--root' argument.

    Args:
        args (argparse.ArgumentParser): Argparse arguments.

    """
    root_directory: str = args.root_directory
    if root_directory is not None:
        rootdir = Path(root_directory).absolute()
        output_step(
            format_str(
                _("Entering directory '${{path}}' ..."),
                fmt={"path": make_pretty(str(rootdir))},
            ),
        )
        os.chdir(rootdir)


def main() -> None:
    """Rubisco main entry point."""
    try:
        clean_logfile()
        logger.info("Rubisco CLI version %s started.", str(APP_VERSION))
        colorama.init()
        bind_ktrigger_interface("rubisco", RubiscoKTrigger())
        load_all_extensions()

        # Register built-in command lines.
        register_builtin_cmds()
        register_extman_cmds()

        args = arg_parser.parse_args()

        set_available_color(args.used_prompt_colors)
        parse_root_argument(args)

        load_project()

        print(get_project_config().hooks)

        op_command = args.command
        if op_command is None:
            op_command = "info"

        args.func(args)
        sys.exit(0)

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
