#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019 - 2021 Fridolin Pokorny
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

"""Test pipeline builder used for building pipeline configuration."""

import os
from typing import Union
from typing import Dict

from flexmock import flexmock
import pytest
from pathlib import Path
import json
import yaml

from thoth.adviser.boot import Boot
from thoth.adviser.enums import DecisionType
from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilder
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.pseudonym import Pseudonym
from thoth.adviser.sieve import Sieve
from thoth.adviser.step import Step
from thoth.adviser.stride import Stride
from thoth.adviser.unit import Unit
from thoth.adviser.wrap import Wrap
from thoth.adviser.exceptions import PipelineConfigurationError
from thoth.adviser.exceptions import UnknownPipelineUnitError
from thoth.python import Project

import tests.units as units

from .base import AdviserTestCase
from .helpers import use_test_units


@pytest.fixture
def builder_context() -> PipelineBuilderContext:
    """Fixture for a builder context."""
    builder_context = PipelineBuilderContext(
        graph=None,
        project=None,
        library_usage=None,
        labels={},
        decision_type=DecisionType.RANDOM,
        recommendation_type=None,
    )
    builder_context.add_unit(units.boots.Boot1())
    builder_context.add_unit(units.pseudonyms.Pseudonym1())
    builder_context.add_unit(units.sieves.Sieve1())
    builder_context.add_unit(units.steps.Step1())
    builder_context.add_unit(units.strides.Stride1())
    builder_context.add_unit(units.wraps.Wrap1())
    return builder_context


class TestPipelineBuilderContext(AdviserTestCase):
    """Test context carried within pipeline builder."""

    def test_is_included(self, builder_context: PipelineBuilderContext) -> None:
        """Test check if the given pipeline unit is included."""
        assert builder_context.is_included(units.boots.Boot1)
        assert not builder_context.is_included(units.boots.Boot2)
        assert builder_context.is_included(units.pseudonyms.Pseudonym1)
        assert not builder_context.is_included(units.pseudonyms.Pseudonym2)
        assert builder_context.is_included(units.sieves.Sieve1)
        assert not builder_context.is_included(units.sieves.Sieve2)
        assert builder_context.is_included(units.steps.Step1)
        assert not builder_context.is_included(units.steps.Step2)
        assert builder_context.is_included(units.strides.Stride1)
        assert not builder_context.is_included(units.strides.Stride2)
        assert builder_context.is_included(units.wraps.Wrap1)
        assert not builder_context.is_included(units.wraps.Wrap2)

    def test_is_adviser_pipeline(self) -> None:
        """Test check for an adviser build context."""
        builder_context = PipelineBuilderContext(
            graph=None,
            project=None,
            library_usage=None,
            decision_type=None,
            recommendation_type=RecommendationType.LATEST,
        )
        assert builder_context.is_adviser_pipeline()
        assert not builder_context.is_dependency_monkey_pipeline()

    def test_is_dependency_monkey_pipeline(self) -> None:
        """Test check for a dependency monkey build context."""
        builder_context = PipelineBuilderContext(
            graph=None,
            project=None,
            library_usage=None,
            decision_type=DecisionType.RANDOM,
            recommendation_type=None,
        )
        assert builder_context.is_dependency_monkey_pipeline()
        assert not builder_context.is_adviser_pipeline()

    def test_invalid_pipeline_builder_context(self) -> None:
        """Test check an invalid build context."""
        # Exactly one from decision type/recommendation type has to be specified.
        with pytest.raises(ValueError):
            PipelineBuilderContext(
                graph=None,
                project=None,
                library_usage=None,
                decision_type=None,
                recommendation_type=None,
            )

        with pytest.raises(ValueError):
            PipelineBuilderContext(
                graph=None,
                project=None,
                library_usage=None,
                decision_type=DecisionType.ALL,
                recommendation_type=RecommendationType.LATEST,
            )

    @pytest.mark.parametrize(
        "unit_class,builder_context_attr",
        [
            (units.boots.Boot2, "boots"),
            (units.pseudonyms.Pseudonym2, "pseudonyms"),
            (units.sieves.Sieve2, "sieves"),
            (units.steps.Step2, "steps"),
            (units.strides.Stride2, "strides"),
            (units.wraps.Wrap2, "wraps"),
        ],
    )
    def test_add_unit(
        self,
        builder_context: PipelineBuilderContext,
        unit_class: Unit,
        builder_context_attr: str,
    ) -> None:
        """Test addition of a unit."""
        assert not builder_context.is_included(unit_class)
        unit = unit_class()
        builder_context.add_unit(unit)
        assert builder_context.is_included(unit_class)
        assert getattr(builder_context, builder_context_attr)[-1] is unit

    def test_get_included_boots(self) -> None:
        """Test get included boots of the provided boot class."""
        builder_context = PipelineBuilderContext(decision_type=DecisionType.RANDOM)
        assert list(builder_context.get_included_boots(units.boots.Boot1)) == []
        assert list(builder_context.get_included_boot_names()) == []
        unit = units.boots.Boot1()
        builder_context.add_unit(unit)
        assert list(builder_context.get_included_boots(units.boots.Boot1)) == [unit]
        assert list(builder_context.get_included_boot_names()) == ["Boot1"]

    def test_get_included_pseudonyms(self) -> None:
        """Test get included pseudonyms of the provided pseudonym class."""
        builder_context = PipelineBuilderContext(decision_type=DecisionType.RANDOM)
        assert list(builder_context.get_included_pseudonyms(units.pseudonyms.Pseudonym1)) == []
        assert list(builder_context.get_included_pseudonym_names()) == []
        unit = units.pseudonyms.Pseudonym1()
        builder_context.add_unit(unit)
        assert list(builder_context.get_included_pseudonyms(units.pseudonyms.Pseudonym1)) == [unit]
        assert list(builder_context.get_included_pseudonym_names()) == ["Pseudonym1"]

    def test_get_included_sieves(self) -> None:
        """Get included sieves of the provided sieve class."""
        builder_context = PipelineBuilderContext(decision_type=DecisionType.RANDOM)
        assert list(builder_context.get_included_sieves(units.sieves.Sieve1)) == []
        assert list(builder_context.get_included_sieve_names()) == []
        unit = units.sieves.Sieve1()
        builder_context.add_unit(unit)
        assert list(builder_context.get_included_sieves(units.sieves.Sieve1)) == [unit]
        assert list(builder_context.get_included_sieve_names()) == ["Sieve1"]

    def test_get_included_steps(self) -> None:
        """Get included steps of the provided step class."""
        builder_context = PipelineBuilderContext(decision_type=DecisionType.RANDOM)
        assert list(builder_context.get_included_steps(units.steps.Step1)) == []
        assert list(builder_context.get_included_step_names()) == []
        unit = units.steps.Step1()
        builder_context.add_unit(unit)
        assert list(builder_context.get_included_steps(units.steps.Step1)) == [unit]
        assert list(builder_context.get_included_step_names()) == ["Step1"]

    def test_get_included_strides(self) -> None:
        """Get included strides of the provided stride class."""
        builder_context = PipelineBuilderContext(decision_type=DecisionType.RANDOM)
        assert list(builder_context.get_included_strides(units.strides.Stride1)) == []
        assert list(builder_context.get_included_stride_names()) == []
        unit = units.strides.Stride1()
        builder_context.add_unit(unit)
        assert list(builder_context.get_included_strides(units.strides.Stride1)) == [unit]
        assert list(builder_context.get_included_stride_names()) == ["Stride1"]

    def test_get_included_wraps(self) -> None:
        """Get included wraps of the provided wrap class."""
        builder_context = PipelineBuilderContext(decision_type=DecisionType.RANDOM)
        assert list(builder_context.get_included_wraps(units.wraps.Wrap1)) == []
        assert list(builder_context.get_included_wrap_names()) == []
        unit = units.wraps.Wrap1()
        builder_context.add_unit(unit)
        assert list(builder_context.get_included_wraps(units.wraps.Wrap1)) == [unit]
        assert list(builder_context.get_included_wrap_names()) == ["Wrap1"]


class TestPipelineBuilder(AdviserTestCase):
    """Tests related to pipeline builder."""

    @use_test_units
    @pytest.mark.parametrize(
        "pipeline_config_method,kwargs",
        [
            (
                "get_adviser_pipeline_config",
                {"recommendation_type": RecommendationType.LATEST},
            ),
            (
                "get_dependency_monkey_pipeline_config",
                {"decision_type": DecisionType.RANDOM},
            ),
        ],
    )
    def test_build_configuration(
        self,
        pipeline_config_method: str,
        kwargs: Dict[str, Union[RecommendationType, DecisionType]],
    ) -> None:
        """Test building configuration."""
        # All test units do not register themselves - let's cherry-pick ones that should be present.
        # There are done 3 iterations in total during pipeline configuration creation.
        flexmock(units.boots.Boot1).should_receive("should_include").and_yield(
            {"some_parameter": 1.0}
        ).and_yield().and_yield().times(3)
        flexmock(units.pseudonyms.Pseudonym2).should_receive("should_include").and_yield(
            {}
        ).and_yield().and_yield().times(3)
        flexmock(units.sieves.Sieve2).should_receive("should_include").and_yield(
            {"foo": "bar"}
        ).and_yield().and_yield().times(3)
        flexmock(units.steps.Step1).should_receive("should_include").and_yield({}).and_yield().and_yield().times(3)
        flexmock(units.strides.Stride2).should_receive("should_include").and_yield({}).and_yield().and_yield().times(3)
        flexmock(units.strides.Stride1).should_receive("should_include").and_yield().and_yield(
            {"linus": "torvalds"}
        ).and_yield().times(3)
        flexmock(units.wraps.Wrap2).should_receive("should_include").and_yield({}).and_yield().and_yield().times(3)

        # It is not relevant if adviser/dependency monkey is called in this case.
        pipeline = getattr(PipelineBuilder, pipeline_config_method)(
            graph=None,
            project=None,
            library_usage=None,
            labels={},
            prescription=None,
            cli_parameters=None,
            **kwargs,
        )

        assert pipeline.to_dict() == {
            "boots": [
                {"name": "Boot1", "configuration": {"some_parameter": 1.0, "package_name": "flask"}, "unit_run": False}
            ],
            "sieves": [
                {
                    "name": "Sieve2",
                    "configuration": {"date": "2015-09-15", "foo": "bar", "package_name": "selinon"},
                    "unit_run": False,
                }
            ],
            "pseudonyms": [{"name": "Pseudonym2", "configuration": {"package_name": "flask"}, "unit_run": False}],
            "steps": [
                {
                    "name": "Step1",
                    "configuration": {
                        "guido_retirement": 2019,
                        "package_name": "tensorflow",
                        "multi_package_resolution": False,
                    },
                    "unit_run": False,
                }
            ],
            "strides": [
                {"name": "Stride2", "configuration": {"foo": None, "package_name": "thamos"}, "unit_run": False},
                {
                    "name": "Stride1",
                    "configuration": {
                        "linus": "torvalds",
                        "package_name": None,
                    },
                    "unit_run": False,
                },
            ],
            "wraps": [{"name": "Wrap2", "configuration": {"package_name": "hexsticker"}, "unit_run": False}],
        }

    @use_test_units
    def test_blocked_units(self, project: Project) -> None:
        """Test preventing a pipeline unit from being added to pipeline configuration."""
        flexmock(units.boots.Boot1).should_receive("should_include").and_yield({}).and_yield().times(2)
        flexmock(units.steps.Step1).should_receive("should_include").and_yield({}).and_yield().times(2)

        pipeline = PipelineBuilder.get_adviser_pipeline_config(
            recommendation_type=RecommendationType.LATEST,
            graph=None,
            project=project,
            labels={},
            library_usage=None,
            prescription=None,
            cli_parameters=None,
        )

        assert len(pipeline.boots) == 1
        assert pipeline.boots[0].__class__ is units.boots.Boot1

        assert len(pipeline.steps) == 1
        assert pipeline.steps[0].__class__ is units.steps.Step1

        assert "THOTH_ADVISER_BLOCKED_UNITS" not in os.environ

        try:
            os.environ["THOTH_ADVISER_BLOCKED_UNITS"] = f"{units.boots.Boot1.__name__},{units.steps.Step1.__name__}"

            flexmock(units.boots.Boot1).should_receive("should_include").times(0)
            flexmock(units.steps.Step1).should_receive("should_include").times(0)

            pipeline = PipelineBuilder.get_adviser_pipeline_config(
                recommendation_type=RecommendationType.LATEST,
                graph=None,
                project=None,
                labels={},
                library_usage=None,
                prescription=None,
                cli_parameters=None,
            )
            assert len(pipeline.boots) == 0
            assert len(pipeline.steps) == 0
        finally:
            os.environ.pop("THOTH_ADVISER_BLOCKED_UNITS")

    @use_test_units
    def test_from_dict(self) -> None:
        """Test instantiation of a pipeline from a dictionary."""
        dict_ = {
            "boots": [
                {"name": "Boot1", "configuration": {"some_parameter": 1.0, "package_name": "flask"}, "unit_run": False}
            ],
            "pseudonyms": [{"name": "Pseudonym2", "configuration": {"package_name": "tensorflow"}, "unit_run": False}],
            "sieves": [
                {
                    "name": "Sieve2",
                    "configuration": {"date": "2015-09-15", "foo": "bar", "package_name": "selinon"},
                    "unit_run": False,
                }
            ],
            "steps": [
                {
                    "name": "Step1",
                    "configuration": {
                        "guido_retirement": 2019,
                        "package_name": "tensorflow",
                        "multi_package_resolution": False,
                    },
                    "unit_run": False,
                }
            ],
            "strides": [
                {"name": "Stride2", "configuration": {"foo": None, "package_name": "thamos"}, "unit_run": False},
                {"name": "Stride1", "configuration": {"linus": "torvalds", "package_name": None}, "unit_run": False},
            ],
            "wraps": [{"name": "Wrap2", "configuration": {"package_name": "hexsticker"}, "unit_run": False}],
        }

        pipeline = PipelineBuilder.from_dict(dict(dict_))
        pipeline_dict = pipeline.to_dict()
        assert pipeline_dict == dict_
        assert isinstance(pipeline.boots[0], Boot)
        assert isinstance(pipeline.pseudonyms[0], Pseudonym)
        assert isinstance(pipeline.sieves[0], Sieve)
        assert isinstance(pipeline.steps[0], Step)
        assert isinstance(pipeline.strides[0], Stride)
        assert isinstance(pipeline.strides[1], Stride)
        assert isinstance(pipeline.wraps[0], Wrap)

    @use_test_units
    def test_load(self, tmp_path: Path) -> None:
        """Test instantiation of a pipeline from a dictionary."""
        expected_dict_ = {
            "boots": [
                {"configuration": {"package_name": "flask", "some_parameter": -0.2}, "name": "Boot1", "unit_run": False}
            ],
            "pseudonyms": [],
            "sieves": [],
            "steps": [
                {
                    "configuration": {
                        "guido_retirement": 2019,
                        "package_name": "tensorflow",
                        "multi_package_resolution": False,
                    },
                    "name": "Step1",
                    "unit_run": False,
                }
            ],
            "strides": [
                {"configuration": {"foo": None, "package_name": "thamos"}, "name": "Stride2", "unit_run": False}
            ],
            "wraps": [],
        }

        dict_ = {
            "boots": [{"name": "Boot1"}],
            "pseudonyms": [],
            "sieves": [],
            "steps": [
                {
                    "name": "Step1",
                    "unit_run": False,
                    "configuration": {"guido_retirement": 2019, "package_name": "tensorflow"},
                }
            ],
            "strides": [{"name": "Stride2", "unit_run": False}],
            "wraps": [],
        }

        yaml_path = tmp_path / "config.yaml"
        with open(str(yaml_path), "w") as f:
            yaml.safe_dump(dict_, f)

        pipeline = PipelineBuilder.load(yaml_path)

        assert isinstance(pipeline.boots[0], Boot)
        assert not pipeline.pseudonyms
        assert not pipeline.sieves
        assert isinstance(pipeline.steps[0], Step)
        assert isinstance(pipeline.strides[0], Stride)
        assert not pipeline.wraps
        pipeline_dict = pipeline.to_dict()
        assert pipeline_dict == expected_dict_

        json_path = tmp_path / "config.json"
        with open(str(json_path), "w") as f:
            json.dump(dict_, f)

        pipeline = PipelineBuilder.load(json_path)
        assert isinstance(pipeline.boots[0], Boot)
        assert not pipeline.pseudonyms
        assert not pipeline.sieves
        assert isinstance(pipeline.steps[0], Step)
        assert isinstance(pipeline.strides[0], Stride)
        assert not pipeline.wraps
        pipeline_dict = pipeline.to_dict()
        assert pipeline_dict == expected_dict_

    @use_test_units
    def test_from_dict_unit_configuration_error(self) -> None:
        """Test instantiation of a pipeline unit in case configuration errors.."""
        dict_ = {
            "boots": [{"name": "Boot1", "configuration": {"foo": "bar"}}],
        }

        flexmock(units.boots.Boot1)
        units.boots.Boot1.should_receive("update_configuration").with_args({"foo": "bar"}).and_raise(ValueError)

        with pytest.raises(PipelineConfigurationError):
            PipelineBuilder.from_dict(dict_)

    @use_test_units
    def test_from_dict_unit_not_exist_error(self) -> None:
        """Test instantiation of a pipeline from a dictionary in case of missing unit."""
        dict_ = {
            "sieves": [{"name": "SieveThatDoesNotExist", "configuration": {"foo": "bar"}}],
        }

        with pytest.raises(UnknownPipelineUnitError):
            PipelineBuilder.from_dict(dict_)
