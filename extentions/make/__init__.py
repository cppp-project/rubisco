# -*- coding: utf-8 -*-
# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2024 The C++ Plus Project.
# This file is part of the repoutils.
#
# repoutils is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# repoutils is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Extention for make.
"""

from repoutils.shared.extention import IRUExtention
from repoutils.lib.variable import push_variables
from repoutils.lib.fileutil import find_command


class MakeExtention(IRUExtention):
    """
    Extention for make.
    """

    name = "make"

    def extention_can_load_now(self, is_auto: bool) -> bool:
        return not is_auto  # Only load when manually requested.

    def on_load(self) -> None:
        make = find_command("make")
        push_variables("MAKE", make)

    def reqs_is_sloved(self) -> bool:
        return True

    def reqs_solve(self) -> None:
        pass


instance = MakeExtention()
