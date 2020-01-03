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

"""Test adviser's context passed to pipeline units."""

import flexmock

from .base import AdviserTestCase

from thoth.adviser.dm_report import DependencyMonkeyReport


class TestDependencyMonkeyReport(AdviserTestCase):
    """Test dependency monkey reporting."""

    def test_to_dict(self) -> None:
        """Check dependency monkey report serialization."""
        report = DependencyMonkeyReport()

        assert report.to_dict() == {"skipped": 0, "responses": []}

        product_dict = {"foo": 1}
        product = flexmock()
        product.should_receive("to_dict").with_args().and_return(product_dict).once()

        response = "assaintuosuco"
        report.skipped += 1
        report.add_response(response, product)

        assert report.to_dict() == {
            "skipped": 1,
            "responses": [{"response": response, "product": product_dict}],
        }

    def test_add_responses(self) -> None:
        """Test adding new responses to report."""
        report = DependencyMonkeyReport()

        assert len(report.to_dict()["responses"]) == 0

        response1 = "assaintuosuco"
        product_dict1 = {"foo": 1}
        product1 = flexmock()
        product1.should_receive("to_dict").with_args().and_return(product_dict1).once()

        report.add_response(response1, product1)
        assert len(report.to_dict()["responses"]) == 1
        assert report.to_dict()["responses"][-1]["response"] == response1
        assert report.to_dict()["responses"][-1]["product"] is product_dict1

        response2 = "epoximise"
        product_dict2 = {"foo": 2}
        product2 = flexmock()
        product2.should_receive("to_dict").with_args().and_return(product_dict2).once()

        report.add_response(response2, product2)
        assert len(report.to_dict()["responses"]) == 2
        assert report.to_dict()["responses"][-2]["response"] == response1
        assert report.to_dict()["responses"][-2]["product"] is product_dict1
        assert report.to_dict()["responses"][-1]["response"] == response2
        assert report.to_dict()["responses"][-1]["product"] is product_dict2
