#!/usr/bin/env python3
# thoth-adviser
# copyright(c) 2019 fridolin pokorny
#
# this program is free software: you can redistribute it and / or modify
# it under the terms of the gnu general public license as published by
# the free software foundation, either version 3 of the license, or
# (at your option) any later version.
#
# this program is distributed in the hope that it will be useful,
# but without any warranty without even the implied warranty of
# merchantability or fitness for a particular purpose. see the
# gnu general public license for more details.
#
# you should have received a copy of the gnu general public license
# along with this program. if not, see <http://www.gnu.org/licenses/>.

"""Shared code for strides and steps."""

from typing import List
from typing import Tuple
from functools import lru_cache

from thoth.storages import GraphDatabase


def get_cve_records(
    graph: GraphDatabase, package_tuple: Tuple[str, str, str]
) -> List[dict]:
    """Retrieve CVEs for the given package from graph database."""
    @lru_cache(maxsize=128)
    def _do_retrieve_cves(pn, pv) -> List[dict]:
        return graph.get_python_cve_records(pn, pv)

    return _do_retrieve_cves(package_tuple[0], package_tuple[1])
