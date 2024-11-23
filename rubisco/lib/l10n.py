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

"""Localization support."""

from __future__ import annotations

import gettext
import locale
import sys

from rubisco.config import TEXT_DOMAIN
from rubisco.lib.l10n_lang_names import LOCALE_NAMES
from rubisco.lib.log import logger
from rubisco.lib.pathlib import Path

__all__ = [
    "_",
    "load_locale_domain",
    "locale_language",
    "locale_language_name",
]


def _locale_language(category: int) -> str | None:
    try:
        return locale.getlocale(category)[0]
    except (ValueError, TypeError):
        return None


def locale_language() -> str:
    """Get locale language.

    Returns:
        str: Locale language.

    """
    return (
        _locale_language(locale.LC_ALL)
        or _locale_language(locale.LC_MESSAGES)
        or _locale_language(locale.LC_CTYPE)
        or _locale_language(locale.LC_NUMERIC)
        or "C"
    )


def locale_language_name() -> str:
    """Get locale language's name.

    Returns:
        str: Locale language name.

    """
    return LOCALE_NAMES.get(locale_language(), _("Unknown"))


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
            domain,
            str(locale_dir),
            [locale_language()],
            fallback=False,
        )
        return True  # noqa: TRY300
    except:  # noqa: E722 # pylint: disable=bare-except
        return False


translations: list[gettext.GNUTranslations] = []
translations_path: list[Path] = []


def load_locale_domain(root_dir: Path, domain: str) -> None:
    """Load locale domain.

    Args:
        root_dir (Path): Gettext objects' directory.
        domain (str): Domain name.

    """
    locale_dir: Path

    possible_dirs = [
        root_dir,
        root_dir / "locale",
        root_dir / ".." / "locale",
        root_dir / "share" / "locale",
    ]
    for onedir in possible_dirs:
        if has_domain(domain, onedir):
            locale_dir = onedir.resolve()
            break
    else:
        logger.debug("Skip domain '%s' in '%s'.", str(domain), str(root_dir))
        return

    try:
        translation = gettext.translation(
            domain,
            str(locale_dir),
            [locale_language()],
            fallback=False,
        )
        translations.append(translation)
        translations_path.append(locale_dir)
        logger.info(
            "Gettext domain '%s' in '%s' loaded.",
            str(domain),
            str(root_dir),
        )
    except:  # noqa: E722 # pylint: disable=bare-except
        logger.warning(
            "Error while loading gettext domain '%s' in '%s'.",
            str(domain),
            str(root_dir),
            exc_info=sys.exc_info(),
        )


# Constants for .
PROGRAM_PATH = Path(sys.argv[0]).resolve()
RES_PATH = Path(getattr(sys, "_MEIPASS", PROGRAM_PATH)).resolve()

# Update locale information.
try:
    # Let's Python use the system's locale.
    locale.setlocale(locale.LC_ALL, "")
except locale.Error:
    # Fallback to C locale if system locale is not available.
    locale.setlocale(locale.LC_ALL, "C")

# Initialize rubisco locales.
load_locale_domain(PROGRAM_PATH, TEXT_DOMAIN)
load_locale_domain(RES_PATH, TEXT_DOMAIN)
load_locale_domain(Path("/usr/share/locale"), TEXT_DOMAIN)
load_locale_domain(Path("/usr/local/share/locale"), TEXT_DOMAIN)


# Gettext function. This function supports multi translations.
def _(message: str) -> str:
    """Translate message by loaded locale domains.

    Args:
        message (str): The message you want to translate.

    Returns:
        str: Translated message. Return message itself if translation failed.

    """
    for translation in translations:
        translated = translation.gettext(message)
        if translated:
            return translated
    return message


if len(translations_path) >= 1:
    gettext.bindtextdomain(TEXT_DOMAIN, translations_path[0])
    gettext.textdomain(TEXT_DOMAIN)

if __name__ == "__main__":
    import os

    sys.stdout.write(f"locale_language(): {locale_language()}\n")
    sys.stdout.write(f"locale_language_name(): {locale_language_name()}\n")
    sys.stdout.write(f"os.strerror(2): {os.strerror(2)}\n")
    sys.stdout.flush()
