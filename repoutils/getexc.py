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
Get excpetion message.
"""

import sys
import traceback
import io

__all__ = ["get_exception_message"]


def get_exception_message():
    """Get more exception infomation message.

    Returns:
        str: The exception message.
    """

    exc_type, exc_value, exc_traceback = sys.exc_info()
    if exc_type is None:  # No exception.
        return ""
    output_file = io.StringIO()
    traceback.print_exception(exc_type, exc_value, exc_traceback, file=output_file)
    return output_file.getvalue()


if __name__ == "__main__":
    print(f"{__file__}: {__doc__.strip()}")

    try:

        def _f1():
            raise RuntimeError("test")

        def _f2():
            _f1()

        try:
            _f2()
        except RuntimeError:
            _f1()
    except RuntimeError:
        print(get_exception_message())

    print("Done.")
