#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2021 Fridolin Pokorny
#
# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Database of CPUs and CPU flags."""

import os
import yaml

from typing import List


class _CPUDatabase:
    """A database of CPUs and CPU flags."""

    _CPU_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "cpu_db.yaml")

    __slots__ = ["_cpu_flags"]

    def __init__(self) -> None:
        """Load and prepare the database."""
        self._cpu_flags = {}

        with open(self._CPU_DB_PATH, "r") as cpu_db:
            content = yaml.load(cpu_db, Loader=yaml.CLoader)

        for flag, cpus in content["flags"].items():
            self._cpu_flags[flag] = frozenset(tuple(i) for i in cpus)

    def provides_flag(self, cpu_model: int, cpu_family: int, flag: str) -> bool:
        """Check if the given CPU provides the given flag."""
        return (cpu_model, cpu_family) in (self._cpu_flags.get(flag) or frozenset())

    def get_known_flags(self) -> List[str]:
        """Get known CPU flags."""
        return list(self._cpu_flags.keys())


CPUDatabase = _CPUDatabase()
