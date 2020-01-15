#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020 Fridolin Pokorny
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

"""Various helpers and utility functions."""

import os
import logging

from typing import Any
from typing import Set


def should_keep_history(value: Any) -> bool:
    """Check if the history should be kept.

    Used as click's converter. If not set explicitly during invocation, check
    environment variable to turn off history tracking. The default value of
    `value' is None which triggers checks in environment variables.
    """
    if value is None:
        return not bool(int(os.getenv("THOTH_ADVISER_NO_HISTORY", 0)))

    if isinstance(value, bool):
        return value

    raise ValueError(
        f"Unknown keep history configuration value: {value!r} if of type {type(value)!r}"
    )


def log_once(
    logger: logging.Logger,
    log_state: Set[object],
    log_state_key: object,
    msg: str,
    *args: object,
    level: int = logging.WARNING,
    **kwargs: object,
) -> None:
    """Log the given message once."""
    if log_state_key in log_state:
        # Already logged, noop.
        return

    log_state.add(log_state_key)
    logger.log(level, msg, *args, **kwargs)
