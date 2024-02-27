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

from enum import Enum
import sys
from typing import Iterable
from tqdm import tqdm
from colorama import init, Fore, Style
from colorama.ansi import code_to_chars
from cppp_repoutils.constants import STDOUT_IS_TTY
from cppp_repoutils.utils.variable import push_variables, format_str


__all__ = ["output", "output_step", "format_str", "ProgressBar"]

init(autoreset=True)

# Colors.
push_variables("red", Fore.RED if STDOUT_IS_TTY else "")
push_variables("yellow", Fore.YELLOW if STDOUT_IS_TTY else "")
push_variables("green", Fore.GREEN if STDOUT_IS_TTY else "")
push_variables("cyan", Fore.CYAN if STDOUT_IS_TTY else "")
push_variables("blue", Fore.BLUE if STDOUT_IS_TTY else "")
push_variables("magenta", Fore.MAGENTA if STDOUT_IS_TTY else "")
push_variables("gray", Fore.LIGHTBLACK_EX if STDOUT_IS_TTY else "")
push_variables("white", Fore.WHITE if STDOUT_IS_TTY else "")
push_variables("reset", code_to_chars(0) if STDOUT_IS_TTY else "")

# Styles.
push_variables("bold", Style.BRIGHT if STDOUT_IS_TTY else "")
push_variables("underline", code_to_chars(4) if STDOUT_IS_TTY else "")
push_variables("blink", code_to_chars(5) if STDOUT_IS_TTY else "")
push_variables("reverse", code_to_chars(7) if STDOUT_IS_TTY else "")
push_variables("hidden", code_to_chars(8) if STDOUT_IS_TTY else "")
push_variables("italic", code_to_chars(3) if STDOUT_IS_TTY else "")


def output(  # pylint: disable=too-many-arguments
    message: str,
    end: str = "\n",
    suffix: str = "",
    fmt: dict[str, str] | None = None,
    color: str = "",
    flush: bool = False,
) -> None:
    """Output a message to the console.

    Args:
        message (str): The message to output.
        end (str, optional): The end of the message. Defaults to "\n".
        suffix (str, optional): The suffix of the message. Defaults to "".
        fmt (dict[str, str], optional): The format of the message.
            Defaults to None.
        color (str, optional): The color of the message. Defaults to "".
        flush (bool, optional): Flush the output. Defaults to False.
    """

    if color:
        message = (
            f"{{{color}}}" + f"{message}" + "{reset}"
        )  # Don't use f-string for {reset}.
    message = format_str(message, fmt)
    message = f"{suffix}{message}{end}"
    sys.stdout.write(message)
    if flush:
        sys.stdout.flush()


def output_step(  # pylint: disable=too-many-arguments
    message: str,
    end: str = "\n",
    suffix: str = "",
    fmt: dict[str, str] | None = None,
    color: str = "",
    flush: bool = False,
) -> None:
    """Output a step message to the console.

    Args:
        message (str): The step message to output.
        end (str, optional): The end of the message. Defaults to "\n".
        suffix (str, optional): The suffix of the message. Defaults to "".
        fmt (dict[str, str], optional): The format of the message.
            Defaults to None.
        color (str, optional): The color of the message. Defaults to "".
        flush (bool, optional): Flush the output. Defaults to False.
    """

    if message:
        output("=> ", end="", color="blue", flush=False)
        output(
            message,
            end=end,
            suffix=suffix,
            fmt=fmt,
            color=color,
            flush=flush,
        )


class _WindowsTaskbarProgressState(Enum):
    """
    Windows taskbar progress state.
    See https://learn.microsoft.com/en-us/windows/terminal/tutorials/progress-bar-sequences. # noqa: E501 # pylint: disable=line-too-long
    """

    HIDDEN = 0
    DEFAULT = 1
    ERROR = 2
    INDETERMINATE = 3
    WARNING = 4


def _windows_taskbar_progress(
    state: _WindowsTaskbarProgressState | int, progress: int
) -> None:
    """Set the Windows taskbar progress.

    Args:
        state (int): State of the progress.
        progress (int): Progress value. 0-100.
    """

    if not STDOUT_IS_TTY:
        return

    if isinstance(state, _WindowsTaskbarProgressState):
        state = state.value

    sys.stdout.write(f"\x1b]9;4;{state};{progress}\a")
    sys.stdout.flush()


class ProgressBar(tqdm):
    """A progress bar."""

    FORMAT_WHITE = format_str(
        "{percentage:3.0f}%|{white}{bar}{reset}| [{n_fmt}/{total_fmt} {rate_fmt}]"  # noqa: E501 # pylint: disable=line-too-long
    )
    FORMAT_BOLDWHITE = format_str(
        "{percentage:3.0f}%|{bold}{white}{bar}{reset}| [{n_fmt}/{total_fmt} {rate_fmt}]"  # noqa: E501 # pylint: disable=line-too-long
    )
    FORMAT_MAGENTA = format_str(
        "{percentage:3.0f}%|{magenta}{bar}{reset}| [{n_fmt}/{total_fmt} {rate_fmt}]"  # noqa: E501 # pylint: disable=line-too-long
    )
    FORMAT_BOLDMAGENTA = format_str(
        "{percentage:3.0f}%|{bold}{magenta}{bar}{reset}| [{n_fmt}/{total_fmt} {rate_fmt}]"  # noqa: E501 # pylint: disable=line-too-long
    )
    FORMAT_YELLOW = format_str(
        "{percentage:3.0f}%|{yellow}{bar}{reset}| [{n_fmt}/{total_fmt} {rate_fmt}]"  # noqa: E501 # pylint: disable=line-too-long
    )
    FORMAT_BOLDYELLOW = format_str(
        "{percentage:3.0f}%|{bold}{yellow}{bar}{reset}| [{n_fmt}/{total_fmt} {rate_fmt}]"  # noqa: E501 # pylint: disable=line-too-long
    )
    FORMAT_CYAN = format_str(
        "{percentage:3.0f}%|{cyan}{bar}{reset}| [{n_fmt}/{total_fmt} {rate_fmt}]"  # noqa: E501 # pylint: disable=line-too-long
    )
    FORMAT_BOLDCYAN = format_str(
        "{percentage:3.0f}%|{bold}{cyan}{bar}{reset}| [{n_fmt}/{total_fmt} {rate_fmt}]"  # noqa: E501 # pylint: disable=line-too-long
    )
    FORMAT_GREEN = format_str(
        "{percentage:3.0f}%|{green}{bar}{reset}| [{n_fmt}/{total_fmt} {rate_fmt}]"  # noqa: E501 # pylint: disable=line-too-long
    )
    FORMAT_BOLDGREEN = format_str(
        "{percentage:3.0f}%|{bold}{green}{bar}{reset}| [{n_fmt}/{total_fmt} {rate_fmt}]"  # noqa: E501 # pylint: disable=line-too-long
    )

    __last_precent: int
    __ignored_precent_sum: int

    def __init__(
        self,
        iterable: Iterable | None = None,
        desc: str | None = None,
        desc_fmt: dict[str, str] | None = None,
        total: float | None = None,
        **kwargs,
    ) -> None:
        """Create a progressbar.

        Args:
            iterable (Iterable | None, optional): Iterable to decorate
                with a progressbar. Defaults to None.
            desc (str | None, optional): Progress description.
                Defaults to None.
            desc_fmt (dict[str, str] | None, optional): The format of
                the message. Defaults to None.
            total (float | None, optional): The number of expected iterations.
                Defaults to None.
        """

        if not STDOUT_IS_TTY:
            self.disable = True

        if desc is not None:
            if desc_fmt is None:
                desc_fmt = {}
            output_step(desc, fmt=desc_fmt)
        _windows_taskbar_progress(
            _WindowsTaskbarProgressState.INDETERMINATE, 0  # noqa: E501
        )
        if not total:
            self.disable = True

        self.__last_precent = 0
        self.__ignored_precent_sum = 0

        super().__init__(
            iterable=iterable,
            total=total,
            desc=desc,
            bar_format=self.FORMAT_WHITE,
            **kwargs,
        )

    def set_progress(self, progress: float) -> bool | None:
        """Set the progress.

        Args:
            progress (float): Progress value.
        """

        delta = progress - self.n

        return self.update(delta)

    def update(self, n: float = 1) -> bool | None:
        """Update the progress.

        Args:
            n (float, optional): The progress value. Defaults to 1.
        """

        if self.disable:
            return None

        current = self.n + n
        percent = int(current / self.total * 100)

        if 1 < percent - self.__last_precent < 1:
            # Ignore small changes.
            self.__last_precent = percent
            self.__ignored_precent_sum += percent
            return None

        percent += self.__ignored_precent_sum
        self.__last_precent = percent
        self.__ignored_precent_sum = 0

        if percent <= 20:
            self.bar_format = self.FORMAT_WHITE
        elif percent <= 30:
            self.bar_format = self.FORMAT_BOLDWHITE
        elif percent <= 40:
            self.bar_format = self.FORMAT_MAGENTA
        elif percent <= 50:
            self.bar_format = self.FORMAT_BOLDMAGENTA
        elif percent <= 60:
            self.bar_format = self.FORMAT_YELLOW
        elif percent <= 70:
            self.bar_format = self.FORMAT_BOLDYELLOW
        elif percent <= 80:
            self.bar_format = self.FORMAT_CYAN
        elif percent <= 90:
            self.bar_format = self.FORMAT_BOLDCYAN
        elif percent <= 95:
            self.bar_format = self.FORMAT_GREEN
        else:
            self.bar_format = self.FORMAT_BOLDGREEN

        _windows_taskbar_progress(
            _WindowsTaskbarProgressState.DEFAULT, int(percent)  # noqa: E501
        )
        return super().update(n)

    def close(self) -> None:
        """Close the progress bar."""

        _windows_taskbar_progress(_WindowsTaskbarProgressState.HIDDEN, 0)
        super().close()


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

    for i in ProgressBar(range(100), desc="Progress"):
        time.sleep(0.01)

    with ProgressBar(desc="Progress 2", total=50) as pbar:
        for i in range(100):
            time.sleep(0.05)
            pbar.update(0.5)
