# -*- coding: utf-8 -*-
# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2024 The C++ Plus Project.
# This file is part of the cppp-repoutils.
#
# cppp-repoutils is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# cppp-repoutils is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Output messages.
"""

import os
import sys

from repoutils.constants import STDOUT_IS_TTY
from repoutils.variable import push_variables, format_string_with_variables


__all__ = ["output", "ProgressBar"]


def init_output():
    """Initialize the output system."""

    if STDOUT_IS_TTY:
        # Colors.
        push_variables("red", "\033[31m")
        push_variables("yellow", "\033[33m")
        push_variables("green", "\033[32m")
        push_variables("cyan", "\033[36m")
        push_variables("blue", "\033[34m")
        push_variables("purple", "\033[35m")
        push_variables("gray", "\033[90m")
        push_variables("white", "\033[37m")
        push_variables("reset", "\033[0m")
        # Styles.
        push_variables("bold", "\033[1m")
        push_variables("underline", "\033[4m")
        push_variables("blink", "\033[5m")
        push_variables("reverse", "\033[7m")
        push_variables("hidden", "\033[8m")
        push_variables("italic", "\033[3m")
    else:
        # Colors.
        push_variables("red", "")
        push_variables("yellow", "")
        push_variables("green", "")
        push_variables("cyan", "")
        push_variables("blue", "")
        push_variables("purple", "")
        push_variables("gray", "")
        push_variables("white", "")
        push_variables("reset", "")
        # Styles.
        push_variables("bold", "")
        push_variables("underline", "")
        push_variables("blink", "")
        push_variables("reverse", "")
        push_variables("hidden", "")
        push_variables("italic", "")


def output(  # pylint: disable=too-many-arguments
    message: str,
    end: str = "\n",
    suffix: str = "",
    fmt: dict[str, str] = None,
    color: str = "",
    flush: bool = False,
):
    """Output a message to the console.

    Args:
        message (str): The message to output.
        end (str, optional): The end of the message. Defaults to "\n".
        suffix (str, optional): The suffix of the message. Defaults to "".
        fmt (dict[str, str], optional): The format of the message. Defaults to None.
        color (str, optional): The color of the message. Defaults to "".
        flush (bool, optional): Flush the output. Defaults to False.
    """

    if color:
        message = (
            f"{{{color}}}" + f"{message}" + "{reset}"
        )  # Don't use f-string for reset.
    message = format_string_with_variables(message, fmt)
    message = f"{suffix}{message}{end}"
    sys.stdout.write(message)
    if flush:
        sys.stdout.flush()

_WIN_TASKBAR_STATE_HIDDEN = 0
_WIN_TASKBAR_STATE_DEFAULT = 1
_WIN_TASKBAR_STATE_ERROR = 2
_WIN_TASKBAR_STATE_INDETERMINATE = 3
_WIN_TASKBAR_STATE_WARNING = 4
def _windows_taskbar_progress(state: int, progress: int):
    """See https://learn.microsoft.com/en-us/windows/terminal/tutorials/progress-bar-sequences"""

    if not STDOUT_IS_TTY:
        return
    sys.stdout.write(f"\x1b]9;4;{state};{progress}\a")
    sys.stdout.flush()

class ProgressBar:
    """A progress bar."""

    __cur: int
    __total: int

    def __init__(self, desc: str, total: int, desc_fmt: dict[str, str] = None):
        """Initialize the progress bar."""

        self.__total = total
        output("=>", end=" ", color="blue")
        output(desc, color="bold", fmt=desc_fmt)
        self.update(0)

    def update(self, cur: int):
        """Update the progress bar.

        Args:
            cur (float): The current progress.
        """

        self.__cur = cur
        if not STDOUT_IS_TTY:
            return

        percent = self.__cur / self.__total
        _windows_taskbar_progress(_WIN_TASKBAR_STATE_DEFAULT, int(percent * 100))
        if percent >= 1:
            _windows_taskbar_progress(_WIN_TASKBAR_STATE_HIDDEN, 0)
        strpercent = f"{percent:.2%} "
        terminal_width = os.get_terminal_size().columns
        bar_width = terminal_width - len(strpercent) - 10
        strbar = "=" * int(bar_width * percent)
        strbar += " " * (bar_width - len(strbar))

        if percent <= 0.2:
            strbar = "{white}" + strbar + "{reset}"
        elif percent <= 0.4:
            strbar = "{yellow}" + strbar + "{reset}"
        elif percent <= 0.8:
            strbar = "{cyan}" + strbar + "{reset}"
        elif percent <= 0.9:
            strbar = "{green}" + strbar + "{reset}"
        else:
            strbar = "{bold}{green}" + strbar + "{reset}"

        output(
            "{bold}{percent}{reset}[{bar}] ",
            end="\r",
            fmt={"percent": strpercent, "bar": strbar},
            flush=True,
        )

    def add(self, delta: int):
        """Add progress to the progress bar.

        Args:
            delta (int): The delta progress.
        """

        self.__cur = self.__cur + delta
        self.update(self.__cur)

    def finish(self):
        """Finish the progress bar."""

        self.update(self.__total)
        output("", end="\n", flush=True)

    def get_total(self) -> int:
        """Get the total progress.

        Returns:
            int: The total progress.
        """

        return self.__total

init_output()  # Call it when import this module.

if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    import time

    output("{red}RED{reset}")
    output("{yellow}YELLOW{reset}")
    output("{green}GREEN{reset}")
    output("{blue}BLUE{reset}")
    output("{purple}PURPLE{reset}")
    output("{cyan}CYAN{reset}")
    output("{gray}GRAY{reset}")
    output("{white}WHITE{reset}")

    output("{bold}BOLD{reset}")
    output("{underline}UNDERLINE{reset}")
    output("{blink}BLINK{reset}")
    output("{reverse}REVERSE{reset}")
    output("{hidden}HIDDEN{reset}(HIDDEN)")
    output("{italic}ITALIC{reset}")

    progbar = ProgressBar("Progress", 100)
    for i in range(100):
        progbar.update(i)
        time.sleep(0.05)
    progbar.finish()
