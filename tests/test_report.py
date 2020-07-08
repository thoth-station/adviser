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

"""Test report as product by a resolver."""

import pytest
import flexmock

from thoth.adviser.pipeline_config import PipelineConfig
from thoth.adviser.product import Product
from thoth.adviser.report import Report
from thoth.common import RuntimeEnvironment

from .base import AdviserTestCase


@pytest.fixture
def pipeline_config() -> PipelineConfig:  # noqa: D401
    """A fixture for a pipeline config."""
    return PipelineConfig(boots=[], sieves=[], steps=[], strides=[], wraps=[])


class TestReport(AdviserTestCase):
    """Test report product by a resolver."""

    def test_stack_info(self, pipeline_config: PipelineConfig) -> None:
        """Test setting a global stack information."""
        report = Report(count=2, pipeline=pipeline_config)
        report.set_stack_info([{"foo": "bar"}])

        assert report.product_count() == 0
        assert report.to_dict() == {
            "pipeline": {"boots": [], "sieves": [], "steps": [], "strides": [], "wraps": [],},
            "products": [],
            "stack_info": [{"foo": "bar"}],
        }

    def test_add_product(self, pipeline_config: PipelineConfig) -> None:
        """Test adding a product to a report."""
        report = Report(count=2, pipeline=pipeline_config)

        product1 = Product(project=None, score=0.42, justification=[], advised_runtime_environment=None)
        report.add_product(product1)
        assert report.product_count() == 1
        assert list(report.iter_products()) == [product1]
        assert list(report.iter_products_sorted()) == [product1]

        product2 = Product(project=None, score=0.0, justification=[], advised_runtime_environment=None)
        report.add_product(product2)
        assert report.product_count() == 2
        assert set(report.iter_products()) == {product1, product2}
        assert list(report.iter_products_sorted()) == [product1, product2]
        assert list(report.iter_products_sorted(reverse=True)) == [product1, product2]
        assert list(report.iter_products_sorted(reverse=False)) == [product2, product1]

        product3 = Product(project=None, score=0.98, justification=[], advised_runtime_environment=None)
        report.add_product(product3)
        assert report.product_count() == 2
        assert set(report.iter_products()) == {product3, product1}
        assert list(report.iter_products_sorted()) == [product3, product1]
        assert list(report.iter_products_sorted(reverse=True)) == [product3, product1]
        assert list(report.iter_products_sorted(reverse=False)) == [product1, product3]

        product4 = Product(project=None, score=0.666, justification=[], advised_runtime_environment=None,)
        report.add_product(product4)
        assert report.product_count() == 2
        assert set(report.iter_products()) == {product3, product4}
        assert list(report.iter_products_sorted()) == [product3, product4]
        assert list(report.iter_products_sorted(reverse=True)) == [product3, product4]
        assert list(report.iter_products_sorted(reverse=False)) == [product4, product3]

    def test_to_dict(self, pipeline_config: PipelineConfig) -> None:
        """Test conversion to a dict."""
        report = Report(count=3, pipeline=pipeline_config)

        project = flexmock()
        project_dict = {"aresto momentum": "avada kedavra"}
        project.should_receive("to_dict").with_args().and_return(project_dict).twice()  # In test and in the report.

        product = Product(
            project=project,
            score=0.666,
            justification=[{"gryffindor": "le gladium leviosa"}],
            advised_runtime_environment=RuntimeEnvironment.from_dict({"python_version": "3.6"}),
        )
        report.add_product(product)

        assert report.product_count() == 1
        assert list(report.iter_products()) == [product]
        assert report.to_dict() == {
            "pipeline": pipeline_config.to_dict(),
            "products": [product.to_dict()],
            "stack_info": None,
        }
