# -*- coding: utf-8 -*-
# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2023 The C++ Plus Project.
# This file is part of the cppp-repoutils.
#
# This file is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# This file is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
NLS (Native Language Support) support module.
"""

import gettext
import locale
from pathlib import Path
from typing import Optional
from cppp_repoutils.constants import TEXT_DOMAIN, PROGRAM_DIR, RESOURCE_PATH

__all__ = ["locale_language", "has_domain", "find_locale_dir", "_"]


def locale_language() -> str:
    """Get locale language.

    Returns:
        str: Locale language.
    """

    return locale.getlocale()[0]


def has_domain(domain: str, locale_dir: Path) -> bool:
    """Check if the domain exists.

    Args:
        domain (str): Domain name.
        locale_dir (Path): Locale directory path.

    Returns:
        bool: True if the domain exists, False otherwise.
    """

    try:
        gettext.translation(
            domain, str(locale_dir), [locale_language()], fallback=False
        )
        return True
    except OSError:
        return False


def _find_locale_dir(root_dir: Path) -> Optional[Path]:
    if has_domain(TEXT_DOMAIN, root_dir):
        return root_dir.resolve()  # <root_dir>
    if has_domain(TEXT_DOMAIN, root_dir / "locale"):
        return (root_dir / "locale").resolve()  # <root_dir>/locale
    if has_domain(TEXT_DOMAIN, root_dir / ".." / "locale"):
        return (root_dir / ".." / "locale").resolve()  # <root_dir>/../locale
    if has_domain(TEXT_DOMAIN, root_dir / "share" / "locale"):
        # <root_dir>/share/locale
        return (root_dir / "share" / "locale").resolve()
    return None


def find_locale_dir() -> Path:
    """Find locale directory.

    Returns:
        Path: Locale directory path.
    """

    locale_dir: Path = Path()
    locale_dir = _find_locale_dir(PROGRAM_DIR)  # Program directory.
    if locale_dir is not None:
        return locale_dir
    locale_dir = _find_locale_dir(RESOURCE_PATH)  # Resource directory.
    if locale_dir is not None:
        return locale_dir
    locale_dir = _find_locale_dir(Path("/usr/share/locale"))  # USR.
    if locale_dir is not None:
        return locale_dir
    locale_dir = _find_locale_dir(
        Path("/usr/local/share/locale")
    )  # System Local Resources.
    return locale_dir if locale_dir is not None else Path()


# Update locale information.
locale.setlocale(locale.LC_ALL, "")  # Let's Python use the system's locale.

# Initialize gettext.

gettext.bindtextdomain(TEXT_DOMAIN, find_locale_dir())
gettext.textdomain(TEXT_DOMAIN)
gettext.install(TEXT_DOMAIN)
_ = gettext.gettext  # Fix undefined name '_' of some IDEs.

if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    import os

    print("locale_language(): ", locale_language())
    print("find_locale_dir(): ", find_locale_dir())
    print("os.strerror(2): ", os.strerror(2))
