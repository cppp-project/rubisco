# -*- coding: utf-8 -*-
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

"""
Extention for make.
"""

import os

from rubisco.shared.extention import IRUExtention
from rubisco.lib.variable import push_variables
from rubisco.lib.fileutil import find_command


class MakeExtention(IRUExtention):
    """
    Extention for make.
    """

    name = "make"

    def extention_can_load_now(self) -> bool:
        return True

    def on_load(self) -> None:
        make = os.getenv("MAKE")
        if not make:
            make = find_command("gmake", strict=False)  # GNU make preferred.
        if not make:
            make = find_command("make")
        if not make:
            make = "make"
        push_variables("MAKE", make)

    def reqs_is_sloved(self) -> bool:
        return True

    def reqs_solve(self) -> None:
        pass


instance = MakeExtention()
