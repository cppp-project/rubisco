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

"""Rubisco changelog generator configs."""

EXTENSION_NAME = "changelog"
LOCALE_DIR_NAME = "locale"

CHANGELOG_FORMAT = """
${{ time }} (${{ time-offset }}) ${{ author }} <${{ email }}>:

$&{{ re.sub(r'^(\\s*)$|^(.*\\S+.*)$',lambda m: '' if m.group(1) is not None \
else f'\\t{m.group(2)}' if m.group(2) is not None else '', g('message'), flags=\
re.MULTILINE) }}

\t* ${{ changed-files }} files changed, +${{ added-lines }}, -${{ removed-lines\
}}""".strip()

TIME_FORMAT = "%Y-%m-%d"
