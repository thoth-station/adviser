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

"""Test Dependency Monkey implementation."""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
import random
import sys
import json

import flexmock
import amun

from thoth.adviser.enums import DecisionType
from thoth.adviser.product import Product
from thoth.adviser.pipeline_config import PipelineConfig
from thoth.adviser.resolver import Resolver
from thoth.adviser.dependency_monkey import DependencyMonkey
from thoth.adviser.dm_report import DependencyMonkeyReport

from .base import AdviserTestCase


class TestDependencyMonkey(AdviserTestCase):
    """Tests related to Dependency Monkey."""

    @staticmethod
    def _get_test_dm(
        *, stack_output: str, with_devel: bool, products: List[Product], amun_context: Optional[Dict[str, Any]] = None
    ) -> DependencyMonkey:
        """Get instantiated dependency monkey ready to be tested."""
        flexmock(Resolver)
        (Resolver.should_receive("resolve_products").with_args(with_devel=with_devel).and_return(products).once())

        flexmock(PipelineConfig)
        (PipelineConfig.should_receive("call_post_run_report").and_return(None).once())

        dependency_monkey = DependencyMonkey(
            resolver=Resolver(pipeline=PipelineConfig(), project=None, library_usage=None, graph=None, predictor=None,),
            stack_output=stack_output,
            decision_type=DecisionType.ALL,
            context=amun_context or {},
        )

        return dependency_monkey

    @staticmethod
    def _get_product_mock() -> Any:
        """Get a mocked product for testing."""

    def test_construct(self) -> None:
        """Test obtaining predictor from Dependency Monkey instance."""
        resolver = flexmock(predictor="foo")
        dependency_monkey = DependencyMonkey(
            resolver=resolver,
            stack_output="-",
            context={"bar": "baz"},
            dry_run=True,
            decision_type=DecisionType.RANDOM,
        )

        assert dependency_monkey.stack_output == "-"
        assert dependency_monkey.context == {"bar": "baz"}
        assert dependency_monkey.dry_run is True
        assert dependency_monkey.decision_type is DecisionType.RANDOM

        # This test actually just makes sure we have predictor property available :)
        assert dependency_monkey.predictor is resolver.predictor

    def test_amun_output(self) -> None:
        """Test Amun API stack submissions."""
        project = flexmock()
        generated_project_dict = {"bar": 1}
        project.should_receive("to_dict").with_args().and_return(generated_project_dict).once()

        product = flexmock(
            project=project,
            score=random.random(),
            justification=[{"justification": "some another justification"}],
            advised_runtime_environment=flexmock(),
        )
        product_dict = {"baz": 2}
        product.should_receive("to_dict").with_args().and_return(product_dict).once()

        amun_api = "http://amun-api"
        amun_context = {"base": "ubi:8"}
        flexmock(amun).should_receive("inspect").with_args(
            amun_api, base=amun_context["base"], python=generated_project_dict
        ).and_return({"inspection_id": "inspection-deadbeef"}).once()

        dependency_monkey = self._get_test_dm(
            stack_output=amun_api, with_devel=True, products=[product], amun_context=amun_context,
        )

        report: DependencyMonkeyReport = dependency_monkey.resolve(with_devel=True)
        assert report.to_dict() == {
            "skipped": 0,
            "responses": [{"response": "inspection-deadbeef", "product": product_dict}],
        }

    def test_dir_output(self) -> None:
        """Test writing output to a directory."""
        project = flexmock()
        project.should_receive("to_files").with_args("/tmp/1/Pipfile", "/tmp/1/Pipfile.lock").and_return(
            {"foo": "bar"}
        ).once()

        product = flexmock(
            project=project,
            score=random.random(),
            justification=[{"justification": "some justification"}],
            advised_runtime_environment=flexmock(),
        )
        product_dict = {"baz": 2}
        product.should_receive("to_dict").with_args().and_return(product_dict).once()

        dependency_monkey = self._get_test_dm(stack_output="/tmp", with_devel=False, products=[product])
        report: DependencyMonkeyReport = dependency_monkey.resolve(with_devel=False)

        assert report.to_dict() == {
            "skipped": 0,
            "responses": [{"response": "/tmp/1", "product": product_dict}],
        }

    def test_stdout_output(self) -> None:
        """Test writing output to standard output."""
        project = flexmock()
        generated_project_dict = {"bar": 1}
        project.should_receive("to_dict").with_args().and_return(generated_project_dict).once()

        product = flexmock(
            project=project,
            score=random.random(),
            justification=[{"justification": "some justification"}],
            advised_runtime_environment=flexmock(),
        )

        dependency_monkey = self._get_test_dm(stack_output="-", with_devel=True, products=[product])
        flexmock(json).should_receive("dump").with_args(
            generated_project_dict, fp=sys.stdout, sort_keys=True, indent=2
        ).and_return(None).once()
        report: DependencyMonkeyReport = dependency_monkey.resolve(with_devel=True)

        # When stdout is used, products are not carried in the final report.
        assert report.to_dict() == {"skipped": 0, "responses": []}
