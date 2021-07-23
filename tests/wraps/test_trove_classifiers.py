#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2021 Fridolin Pokorny
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

"""Test wrap that provides information derived from Python trove classifiers."""

import pytest
from typing import Dict
from typing import List
from typing import Optional
from thoth.common import get_justification_link as jl
from thoth.adviser.context import Context
from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.state import State
from thoth.adviser.wraps import TroveClassifiersWrap

from ..base import AdviserUnitTestCase


class TestTroveClassifiersWrap(AdviserUnitTestCase):
    """Test wrap that provides information derived from Python trove classifiers."""

    UNIT_TESTED = TroveClassifiersWrap

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        self.verify_multiple_should_include(builder_context)

    def test_run_classifiers(self, state: State, context: Context) -> None:
        """Test running and assigning all the classifiers."""
        trove_classifiers = [
            "Development Status:: 3 - Alpha",
            "Development Status:: 7 - Inactive",
            "Environment :: GPU :: NVIDIA CUDA",
            "Environment :: GPU :: NVIDIA CUDA :: 11.2",
            "Environment :: GPU :: NVIDIA CUDA :: 9.2",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3 :: Only",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.9",
        ]

        package_name = "tensorflow-gpu"
        package_version = "2.6.0"
        index_url = "https://pypi.org/simple"

        context.recommendation_type = RecommendationType.STABLE
        context.project.runtime_environment.cuda_version = "10.2"
        context.project.runtime_environment.python_version = "3.8"
        context.graph.should_receive("get_python_package_version_trove_classifiers_all").with_args(
            package_name=package_name,
            package_version=package_version,
            index_url=index_url,
            os_name=context.project.runtime_environment.operating_system.name,
            os_version=context.project.runtime_environment.operating_system.version,
            python_version=context.project.runtime_environment.python_version,
        ).and_return(trove_classifiers).once()

        state.justification.clear()

        unit = self.UNIT_TESTED()
        unit.pre_run()

        state.resolved_dependencies.clear()
        state.add_resolved_dependency((package_name, package_version, index_url))

        with unit.assigned_context(context):
            unit.run(state)

        assert state.justification == [
            {
                "link": jl("trove_cuda"),
                "message": "No CUDA specific trove classifier matching CUDA version used '10.2'",
                "package_name": package_name,
                "type": "WARNING",
            },
            {
                "link": jl("trove_unstable"),
                "message": "Development status stated in trove classifiers is 'alpha' which "
                "might be not suitable to be used with recommendation type "
                "'stable'",
                "package_name": "tensorflow-gpu",
                "type": "WARNING",
            },
            {
                "link": jl("trove_inactive"),
                "message": f"Inactive development status of {package_name!r} stated in trove " "classifiers",
                "package_name": package_name,
                "type": "WARNING",
            },
            {
                "link": jl("trove_py"),
                "message": "No Python specific trove classifier matching Python version used '3.8'",
                "package_name": package_name,
                "type": "WARNING",
            },
        ]

    @pytest.mark.parametrize(
        "cuda_version,trove_classifiers,justification",
        [
            (
                "10.2",
                ["Environment :: GPU :: NVIDIA CUDA :: 9.2", "Environment :: GPU :: NVIDIA CUDA :: 11.2"],
                [
                    {
                        "link": jl("trove_cuda"),
                        "message": "No CUDA specific trove classifier matching CUDA version used '10.2'",
                        "package_name": "tensorflow-gpu",
                        "type": "WARNING",
                    }
                ],
            ),
            (
                None,
                ["Environment :: GPU :: NVIDIA CUDA :: 11.0"],
                [],
            ),
            (
                "10.2",
                ["Environment :: GPU :: NVIDIA CUDA :: 9.2", "Environment :: GPU :: NVIDIA CUDA :: 10.2"],
                [],
            ),
        ],
    )
    def test_environment_gpu_cuda_version(
        self,
        cuda_version: Optional[str],
        trove_classifiers: List[str],
        context: Context,
        state: State,
        justification: List[Dict[str, str]],
    ) -> None:
        """Test adding justifications for environment GPU CUDA version."""
        package_name = "tensorflow-gpu"
        package_version = "2.6.0"
        index_url = "https://pypi.org/simple"

        context.project.runtime_environment.cuda_version = cuda_version
        context.graph.should_receive("get_python_package_version_trove_classifiers_all").with_args(
            package_name=package_name,
            package_version=package_version,
            index_url=index_url,
            os_name=context.project.runtime_environment.operating_system.name,
            os_version=context.project.runtime_environment.operating_system.version,
            python_version=context.project.runtime_environment.python_version,
        ).and_return(trove_classifiers).once()

        state.justification.clear()

        unit = self.UNIT_TESTED()
        unit.pre_run()

        state.resolved_dependencies.clear()
        state.add_resolved_dependency((package_name, package_version, index_url))

        with unit.assigned_context(context):
            unit.run(state)

        assert state.justification == justification

    @pytest.mark.parametrize(
        "development_status_classifiers,recommendation_type,justification",
        [
            ([" Development Status:: 1 - Planning  "], RecommendationType.TESTING, []),
            ([" Development Status:: 2 - Pre - Alpha "], RecommendationType.TESTING, []),
            (["Development Status:: 3 - Alpha"], RecommendationType.TESTING, []),
            (["Development Status:: 4 - Beta"], RecommendationType.TESTING, []),
            (
                ["Development Status:: 5 - Production / Stable"],
                RecommendationType.TESTING,
                [],
            ),
            (["Development Status:: 1 - Planning"], RecommendationType.LATEST, []),
            (["Development Status:: 2 - Pre - Alpha"], RecommendationType.LATEST, []),
            (["Development Status:: 3 - Alpha"], RecommendationType.LATEST, []),
            (["Development Status:: 4 - Beta"], RecommendationType.LATEST, []),
            (
                ["Development Status:: 5 - Production / Stable"],
                RecommendationType.LATEST,
                [],
            ),
            (
                ["Development Status:: 1 - Planning"],
                RecommendationType.STABLE,
                [
                    {
                        "link": jl("trove_unstable"),
                        "message": "Development status stated in trove classifiers is 'planning' "
                        "which might be not suitable to be used with recommendation type "
                        "'stable'",
                        "package_name": "thoth-common",
                        "type": "WARNING",
                    }
                ],
            ),
            (
                ["Development Status:: 2 - Pre - Alpha"],
                RecommendationType.PERFORMANCE,
                [
                    {
                        "link": jl("trove_unstable"),
                        "message": "Development status stated in trove classifiers is 'pre-alpha' "
                        "which might be not suitable to be used with recommendation type "
                        "'performance'",
                        "package_name": "thoth-common",
                        "type": "WARNING",
                    }
                ],
            ),
            (
                ["Development Status:: 3 - Alpha"],
                RecommendationType.STABLE,
                [
                    {
                        "link": jl("trove_unstable"),
                        "message": "Development status stated in trove classifiers is 'alpha' "
                        "which might be not suitable to be used with recommendation type "
                        "'stable'",
                        "package_name": "thoth-common",
                        "type": "WARNING",
                    }
                ],
            ),
            (
                ["Development Status:: 4 - Beta"],
                RecommendationType.SECURITY,
                [
                    {
                        "link": jl("trove_unstable"),
                        "message": "Development status stated in trove classifiers is 'beta' "
                        "which might be not suitable to be used with recommendation type "
                        "'security'",
                        "package_name": "thoth-common",
                        "type": "WARNING",
                    }
                ],
            ),
            (
                ["Development Status:: 5 - Production / Stable"],
                RecommendationType.STABLE,
                [],
            ),
            (
                ["Development Status:: 6 - Mature"],
                RecommendationType.STABLE,
                [],
            ),
        ],
    )
    def test_development_status(
        self,
        development_status_classifiers: List[str],
        recommendation_type: RecommendationType,
        justification: List[Dict[str, str]],
        state: State,
        context: Context,
    ) -> None:
        """Test adding justifications for development status."""
        package_name = "thoth-common"
        package_version = "0.26.0"
        index_url = "https://pypi.org/simple"

        context.graph.should_receive("get_python_package_version_trove_classifiers_all").with_args(
            package_name=package_name,
            package_version=package_version,
            index_url=index_url,
            os_name=context.project.runtime_environment.operating_system.name,
            os_version=context.project.runtime_environment.operating_system.version,
            python_version=context.project.runtime_environment.python_version,
        ).and_return(development_status_classifiers).once()
        context.recommendation_type = recommendation_type

        state.justification.clear()

        unit = self.UNIT_TESTED()
        unit.pre_run()

        state.resolved_dependencies.clear()
        state.add_resolved_dependency((package_name, package_version, index_url))

        with unit.assigned_context(context):
            unit.run(state)

        assert state.justification == justification

    @pytest.mark.parametrize("recommendation_type", list(RecommendationType.__members__.values()))
    def test_development_status_inactive(
        self,
        recommendation_type: RecommendationType,
        state: State,
        context: Context,
    ) -> None:
        """Test adding justifications for inactive development status."""
        package_name = "argparse"
        package_version = "1.4.0"
        index_url = "https://pypi.org/simple"

        development_status_classifiers = ["Development Status:: 7 - Inactive"]

        context.recommendation_type = recommendation_type
        context.graph.should_receive("get_python_package_version_trove_classifiers_all").with_args(
            package_name=package_name,
            package_version=package_version,
            index_url=index_url,
            os_name=context.project.runtime_environment.operating_system.name,
            os_version=context.project.runtime_environment.operating_system.version,
            python_version=context.project.runtime_environment.python_version,
        ).and_return(development_status_classifiers).once()

        state.justification.clear()

        unit = self.UNIT_TESTED()
        unit.pre_run()

        state.resolved_dependencies.clear()
        state.add_resolved_dependency((package_name, package_version, index_url))

        with unit.assigned_context(context):
            unit.run(state)

        assert state.justification == [
            {
                "link": jl("trove_inactive"),
                "message": f"Inactive development status of {package_name!r} stated in trove classifiers",
                "package_name": package_name,
                "type": "WARNING",
            }
        ]

    @pytest.mark.parametrize(
        "python_version,justification",
        [
            (
                "3.6",
                [
                    {
                        "link": jl("trove_py"),
                        "message": "No Python specific trove classifier matching Python version used '3.6'",
                        "package_name": "tensorflow",
                        "type": "WARNING",
                    }
                ],
            ),
            (
                "3.8",
                [],
            ),
            (
                None,
                [],
            ),
        ],
    )
    def test_programming_language_python(
        self, python_version: Optional[str], justification: List[Dict[str, str]], state: State, context: Context
    ) -> None:
        """Test adding justifications for Python programming language."""
        trove_classifiers = [
            "  Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9  ",
            "Programming Language :: Python :: 3.10",
        ]

        package_name = "tensorflow"
        package_version = "2.6.0"
        index_url = "https://pypi.org/simple"

        context.project.runtime_environment.python_version = python_version
        context.graph.should_receive("get_python_package_version_trove_classifiers_all").with_args(
            package_name=package_name,
            package_version=package_version,
            index_url=index_url,
            os_name=context.project.runtime_environment.operating_system.name,
            os_version=context.project.runtime_environment.operating_system.version,
            python_version=context.project.runtime_environment.python_version,
        ).and_return(trove_classifiers).once()

        state.justification.clear()

        unit = self.UNIT_TESTED()
        unit.pre_run()

        state.resolved_dependencies.clear()
        state.add_resolved_dependency((package_name, package_version, index_url))

        with unit.assigned_context(context):
            unit.run(state)

        assert state.justification == justification

    def test_unknown_trove_classifiers(self, state: State, context: Context) -> None:
        """Test not adding justifications for unknown trove classifiers."""
        trove_classifiers = [
            "2323938",
            " Language :: Python :: 3.9  ",
            " Foo: bar",
            "Environment :: GPU :: NVIDIA CUDA :: 9.2.32",
        ]

        package_name = "cowsay"
        package_version = "1.0.0"
        index_url = "https://pypi.org/simple"

        context.project.runtime_environment.python_version = "3.9"
        context.project.runtime_environment.cuda_version = "10.0"
        context.graph.should_receive("get_python_package_version_trove_classifiers_all").with_args(
            package_name=package_name,
            package_version=package_version,
            index_url=index_url,
            os_name=context.project.runtime_environment.operating_system.name,
            os_version=context.project.runtime_environment.operating_system.version,
            python_version=context.project.runtime_environment.python_version,
        ).and_return(trove_classifiers).once()

        state.justification.clear()

        unit = self.UNIT_TESTED()
        unit.pre_run()

        state.resolved_dependencies.clear()
        state.add_resolved_dependency((package_name, package_version, index_url))

        with unit.assigned_context(context):
            unit.run(state)

        assert state.justification == []
