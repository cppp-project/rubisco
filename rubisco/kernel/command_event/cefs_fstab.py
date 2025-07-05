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

"""CommandEventFS fstab support.

CEFS fstab is a multi-line string that represents where the external
command will be mounted.

The format of a line is: `<external command> <mount point>`. Escape characters
in double-quotes is allowed.


Example:
```text
gmake /gmake
"apt upgrade"    /ext/apt-upgrade
```

After it's mounted, we can use Rubisco by following commands:

```bash
rubisco gmake -B -j8  # Same as `gmake -B -j8`
rubisco ext apt-upgrade   # Same as `apt upgrade`
```

"""

import shlex
from pathlib import Path

from rubisco.config import DEFAULT_CHARSET
from rubisco.kernel.command_event.event_path import EventPath
from rubisco.lib.exceptions import RUValueError
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.variable.fast_format_str import fast_format_str

__all__ = ["mount_fstab"]


def parse_fstab(fstab: str) -> dict[EventPath, str]:
    """Parse fstab string.

    Args:
        fstab: The fstab string.

    Returns:
        A dict of external command to mount point. **Key is the mount point,
        value is the external command.**

    """
    fstab_dict: dict[EventPath, str] = {}
    for line_ in fstab.splitlines():
        line = line_.strip()
        if line.startswith("#"):
            continue
        try:
            cmd, mount_point = shlex.split(line)
        except ValueError as exc:
            logger.warning("Parsing fstab line failed: %s", line, exc_info=True)
            raise RUValueError(
                fast_format_str(
                    _("Parsing failed: {{line}}"),
                    fmt={
                        "line": line,
                    },
                ),
            ) from exc
        fstab_dict[EventPath(mount_point)] = cmd
    return fstab_dict


def mount_from_parsed_fstab(fstab: dict[EventPath, str]) -> None:
    """Mount command event from parsed fstab.

    Args:
        fstab: The parsed fstab dict.

    """
    for mount_point, cmd in fstab.items():
        mount_point.mount(cmd)


def mount_fstab(fstab: str | Path) -> None:
    """Mount command event from fstab.

    Args:
        fstab: The fstab string or path.

    """
    if isinstance(fstab, Path):
        fstab = fstab.read_text(encoding=DEFAULT_CHARSET)
    fstab_dict = parse_fstab(fstab)
    mount_from_parsed_fstab(fstab_dict)
