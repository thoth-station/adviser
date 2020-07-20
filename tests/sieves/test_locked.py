#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019, 2020 Fridolin Pokorny
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

"""Test removing pinned versions in direct dependencies."""

import flexmock

from thoth.adviser.sieves import CutLockedSieve
from thoth.python import Source
from thoth.python import PackageVersion
from thoth.python import Project

from ..base import AdviserTestCase


class TestCutPreReleasesSieve(AdviserTestCase):
    """Test removing pinned versions in direct dependencies."""

    _CASE_PIPFILE_LOCKED = """
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
tensorflow = "==1.9.0"

[dev-packages]
pytest = "==5.3.1"
"""

    _CASE_PIPFILE_NOT_LOCKED = """
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
tensorflow = "*"

[dev-packages]
pytest = "*"

[pipenv]
allow_prereleases = true
"""

    def test_cut_locked(self) -> None:
        """Test removing a locked package based on direct dependencies."""
        tf = PackageVersion(
            name="tensorflow", version="==2.0.0", index=Source("https://pypi.org/simple"), develop=False,
        )

        context = flexmock(project=Project.from_strings(self._CASE_PIPFILE_LOCKED))
        with CutLockedSieve.assigned_context(context):
            sieve = CutLockedSieve()
            assert list(sieve.run(p for p in [tf])) == []

    def test_cut_locked_dev(self) -> None:
        """Test removing a locked package based on direct dev dependencies."""
        pytest = PackageVersion(
            name="pytest", version="==2.0.0", index=Source("https://pypi.org/simple"), develop=False,
        )

        context = flexmock(project=Project.from_strings(self._CASE_PIPFILE_LOCKED))
        with CutLockedSieve.assigned_context(context):
            sieve = CutLockedSieve()
            assert list(sieve.run(p for p in [pytest])) == []

    def test_no_cut(self) -> None:
        """Test not removing a locked package based on direct dependencies."""
        tf = PackageVersion(
            name="tensorflow", version="==1.9.0", index=Source("https://pypi.org/simple"), develop=False,
        )

        context = flexmock(project=Project.from_strings(self._CASE_PIPFILE_LOCKED))
        with CutLockedSieve.assigned_context(context):
            sieve = CutLockedSieve()
            assert list(sieve.run(p for p in [tf])) == [tf]

    def test_no_cut_dev(self) -> None:
        """Test not removing a locked package based on dev direct dependencies."""
        pytest = PackageVersion(
            name="pytest", version="==5.3.1", index=Source("https://pypi.org/simple"), develop=False,
        )

        context = flexmock(project=Project.from_strings(self._CASE_PIPFILE_LOCKED))
        with CutLockedSieve.assigned_context(context):
            sieve = CutLockedSieve()
            assert list(sieve.run(p for p in [pytest])) == [pytest]

    def test_noop(self) -> None:
        """Test no operation if dependencies are not locked."""
        tf = PackageVersion(
            name="tensorflow", version="==1.9.0", index=Source("https://pypi.org/simple"), develop=False,
        )

        context = flexmock(project=Project.from_strings(self._CASE_PIPFILE_NOT_LOCKED))
        with CutLockedSieve.assigned_context(context):
            sieve = CutLockedSieve()
            assert list(sieve.run(p for p in [tf])) == [tf]

    def test_noop_dev(self) -> None:
        """Test no operation if dependencies are not locked."""
        pytest = PackageVersion(
            name="pytest", version="==5.3.1", index=Source("https://pypi.org/simple"), develop=False,
        )

        context = flexmock(project=Project.from_strings(self._CASE_PIPFILE_NOT_LOCKED))
        with CutLockedSieve.assigned_context(context):
            sieve = CutLockedSieve()
            assert list(sieve.run(p for p in [pytest])) == [pytest]
