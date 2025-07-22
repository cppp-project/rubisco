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

"""OSC 9 output utilities.

See https://learn.microsoft.com/zh-cn/windows/terminal/tutorials/progress-bar-sequences
"""

import atexit
import sys
from enum import Enum

from rubisco.config import DEFAULT_CHARSET

__all__ = ["ProgressBarState", "conemu_progress"]


class ProgressBarState(Enum):
    """ConEmu progress bar states."""

    DEFAULT = 0
    NORMAL = 1
    ERROR = 2
    WAITING = 3
    WARNING = 4


def conemu_progress(
    state: ProgressBarState,
    current_progress: float = 0,
    total: float = 0,
) -> None:
    """Update ConEmu OSC 9 progress bar state (For Windows Terminal).

    Args:
        state (ProgressBarState): Current state.
        current_progress (float): The current progress.
        total (float): Total value.

    """
    progress = current_progress / total * 100 if total else 50
    if state is ProgressBarState.DEFAULT:
        progress = 0
    msg = f"\x1b]9;4;{state.value};{int(progress)};\x07"
    sys.stdout.buffer.write(msg.encode(DEFAULT_CHARSET))


def reset_progress() -> None:
    """Reset OSC 9 proress bar."""
    conemu_progress(ProgressBarState.DEFAULT)


atexit.register(reset_progress)
