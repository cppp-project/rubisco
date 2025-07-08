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

"""Rubisco localization API.

Some extension may have their own localization files.
You can use this API to load your localization files.
We only support GNU gettext format now.
"""

from rubisco.lib.l10n import (
    _ as gettext,
)
from rubisco.lib.l10n import (
    load_locale_domain,
    locale_language,
    locale_language_name,
)

__all__ = [
    "_",
    "gettext",
    "load_locale_domain",
    "locale_language",
    "locale_language_name",
]

_ = gettext
