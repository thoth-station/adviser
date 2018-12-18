#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2018 Fridolin Pokorny
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

import logging

_LOGGER = logging.getLogger(__name__)


class RuntimeEnvironment:
    """Representation of a runtime environment."""

    def __init__(self, *, cpu_family: int = None, cpu_model: int = None):
        """Construct a runtime environmnet representative."""
        self.cpu_family = cpu_family
        self.cpu_model = cpu_model

    @classmethod
    def from_dict(cls, dict_: dict):
        """Instantiate runtime environment from its dictionary representation."""
        dict_ = dict(dict_)

        instance = cls(
            cpu_family=dict_.pop("cpu_family", None),
            cpu_model=dict_.pop("cpu_model", None),
        )

        if dict_:
            _LOGGER.warning("Unsupported runtime environment entries: %s", dict_)

        return instance

    def to_dict(self):
        """Convert runtime environment object representation to a dict."""
        result = {}
        for attribute, value in self.__dict__.items():
            if value is not None:
                result[attribute] = value
