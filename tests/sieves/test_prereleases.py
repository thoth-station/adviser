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

"""Test removing pre-releases in direct dependencies."""

import flexmock

from thoth.adviser.sieves import CutPreReleasesSieve
from thoth.python import Source
from thoth.python import PackageVersion
from thoth.python import Project

from ..base import AdviserTestCase


class TestCutPreReleasesSieve(AdviserTestCase):
    """Test removing dependencies based on pre-releases configuration."""

    _CASE_DISALLOWED_PIPFILE = """
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[[source]]
url = "https://tensorflow.pypi.thoth-station.ninja/index/os/fedora/30/jemalloc/simple/"
verify_ssl = true
name = "aicoe"

[packages]
tensorflow = "*"

[pipenv]
allow_prereleases = false
"""

    _CASE_ALLOWED_PIPFILE = """
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[[source]]
url = "https://tensorflow.pypi.thoth-station.ninja/index/os/fedora/30/jemalloc/simple/"
verify_ssl = true
name = "aicoe"

[packages]
tensorflow = "*"

[pipenv]
allow_prereleases = true
"""

    def test_remove_pre_releases_allowed_noop(self) -> None:
        """Test removing dependencies not hitting limit causes a noop."""
        tf_2_0_0rc = PackageVersion(
            name="tensorflow", version="==2.0.0rc0", index=Source("https://pypi.org/simple"), develop=False,
        )

        context = flexmock(project=Project.from_strings(self._CASE_ALLOWED_PIPFILE))
        with CutPreReleasesSieve.assigned_context(context):
            sieve = CutPreReleasesSieve()
            assert list(sieve.run(p for p in [tf_2_0_0rc])) == [tf_2_0_0rc]

    def test_pre_releases_disallowed_noop(self) -> None:
        """Test no removals if pre-releases are allowed."""
        tf_2_0_0 = PackageVersion(
            name="tensorflow",
            version="==2.0.0",
            index=Source("https://tensorflow.pypi.thoth-station.ninja/index/os/fedora/30/jemalloc/simple/"),
            develop=False,
        )

        context = flexmock(project=Project.from_strings(self._CASE_DISALLOWED_PIPFILE))
        with CutPreReleasesSieve.assigned_context(context):
            sieve = CutPreReleasesSieve()
            assert list(sieve.run(p for p in [tf_2_0_0])) == [tf_2_0_0]

    def test_pre_releases_disallowed_removal(self) -> None:
        """Test no removals if pre-releases are allowed."""
        tf_2_0_0rc0 = PackageVersion(
            name="tensorflow",
            version="==2.0.0rc0",
            index=Source("https://tensorflow.pypi.thoth-station.ninja/index/os/fedora/30/jemalloc/simple/"),
            develop=False,
        )

        context = flexmock(project=Project.from_strings(self._CASE_DISALLOWED_PIPFILE))
        with CutPreReleasesSieve.assigned_context(context):
            sieve = CutPreReleasesSieve()
            assert list(sieve.run(p for p in [tf_2_0_0rc0])) == []
