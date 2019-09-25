#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019 Fridolin Pokorny
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

import pytest

from base import AdviserTestCase

from thoth.adviser.python.pipeline.sieves import CutPreReleasesSieve
from thoth.adviser.python.pipeline.sieve_context import SieveContext
from thoth.adviser.python.pipeline.exceptions import CannotRemovePackage
from thoth.python import Source
from thoth.python import PackageVersion
from thoth.python import Project


class TestCutPreReleasesSieve(AdviserTestCase):
    """Test removing direct dependencies based on latest version limitation."""

    _CASE_PIPFILE = """
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[[source]]
url = "https://tensorflow.pypi.thoth-station.ninja/index/os/fedora/30/jemalloc/simple/"
verify_ssl = true
name = aicoe

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
name = aicoe

[packages]
tensorflow = "*"

[pipenv]
allow_prereleases = false
"""

    def test_remove_pre_releases(self):
        """Test removing direct dependencies not hitting limit causes a noop."""
        tf_1_1_0 = PackageVersion(
            name="tensorflow",
            version="==1.1.0",
            index=Source("https://tensorflow.pypi.thoth-station.ninja/index/os/fedora/30/jemalloc/simple/"),
            develop=False,
        )
        tf_2_0_0rc = PackageVersion(
            name="tensorflow",
            version="==2.0.0rc0",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        sieve = CutPreReleasesSieve(graph=None, project=Project.from_strings(self._CASE_PIPFILE))
        sieve_context = SieveContext.from_package_versions([tf_1_1_0, tf_2_0_0rc])
        sieve.run(sieve_context)
        result = list(sieve_context.iter_direct_dependencies())
        assert result == [tf_1_1_0]

    def test_remove_pre_releases_error(self):
        """Test error when removing all packages of a type which are pre-releases from software stack."""
        tf_2_0_0rc0 = PackageVersion(
            name="tensorflow",
            version="==2.0.0rc0",
            index=Source("https://tensorflow.pypi.thoth-station.ninja/index/os/fedora/30/jemalloc/simple/"),
            develop=False,
        )
        tf_2_0_0rc1 = PackageVersion(
            name="tensorflow",
            version="==2.0.0rc1",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        sieve = CutPreReleasesSieve(graph=None, project=Project.from_strings(self._CASE_PIPFILE))
        sieve_context = SieveContext.from_package_versions([tf_2_0_0rc0, tf_2_0_0rc1])

        with pytest.raises(CannotRemovePackage):
            sieve.run(sieve_context)

    def test_pre_releases_allowed(self):
        """Test no removals if pre-releases are allowed."""
        tf_2_0_0rc0 = PackageVersion(
            name="tensorflow",
            version="==2.0.0rc0",
            index=Source("https://tensorflow.pypi.thoth-station.ninja/index/os/fedora/30/jemalloc/simple/"),
            develop=False,
        )
        tf_2_0_0rc1 = PackageVersion(
            name="tensorflow",
            version="==2.0.0rc1",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        sieve = CutPreReleasesSieve(graph=None, project=Project.from_strings(self._CASE_ALLOWED_PIPFILE))
        sieve_context = SieveContext.from_package_versions([tf_2_0_0rc0, tf_2_0_0rc1])
        result = list(sieve_context.iter_direct_dependencies())
        assert result == [tf_2_0_0rc0, tf_2_0_0rc1]
