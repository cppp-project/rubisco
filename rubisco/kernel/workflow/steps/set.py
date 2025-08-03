# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2025 The C++ Plus Project.
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

"""SetvarStep, PopvarStep implementation."""

from rubisco.kernel.workflow.step import Step
from rubisco.lib.variable.format import format_str
from rubisco.lib.variable.variable import pop_variables, push_variables

__all__ = ["PopvarStep", "SetvarStep"]


class SetvarStep(Step):
    """Set a variable."""

    var_name: str
    var_value: object

    def init(self) -> None:
        """Initialize the step."""
        self.var_name = self.raw_data.get("var", valtype=str)
        self.var_value = self.raw_data.get("value", valtype=object)

    def run(self) -> None:
        """Run the step."""
        push_variables(
            self.var_name,
            format_str(self.var_value),
        )


class PopvarStep(Step):
    """Pop a variable."""

    var_name: str

    def init(self) -> None:
        """Initialize the step."""
        self.var_name = self.raw_data.get("popvar", valtype=str)

    def run(self) -> None:
        """Run the step."""
        pop_variables(self.var_name)
