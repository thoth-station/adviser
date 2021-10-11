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

"""Test implementation of generic v1 prescription unit handling."""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import flexmock
import pytest

from thoth.adviser.enums import RecommendationType
from thoth.adviser.enums import DecisionType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.prescription.v1 import UnitPrescription
from thoth.adviser.prescription.v1.schema import (
    PRESCRIPTION_UNIT_SHOULD_INCLUDE_SCHEMA,
    PRESCRIPTION_UNIT_SHOULD_INCLUDE_RUNTIME_ENVIRONMENTS_SCHEMA,
)
from thoth.common import get_justification_link as jl
from thoth.common import RuntimeEnvironment

from ...base import AdviserTestCase


class TestUnitPrescription(AdviserTestCase):
    """Test implementation of generic v1 prescription unit handling."""

    _EXAMPLE_RPM_PACKAGES_PRESENT = [
        {
            "arch": "x86_64",
            "epoch": None,
            "package_identifier": "zlib-1.2.11-16.2.el8_3.x86_64",
            "package_name": "zlib",
            "package_version": "1.2.11",
            "release": "16.2.el8_3",
            "src": False,
        },
        {
            "arch": "x86_64",
            "epoch": None,
            "package_identifier": "glib2-2.56.4-8.el8.x86_64",
            "package_name": "glib2",
            "package_version": "2.56.4",
            "release": "8.el8",
            "src": False,
        },
        {
            "arch": "x86_64",
            "epoch": None,
            "package_identifier": "gcc-8.3.1-5.1.el8.x86_64",
            "package_name": "gcc",
            "package_version": "8.3.1",
            "release": "5.1.el8",
            "src": False,
        },
        {
            "arch": "x86_64",
            "epoch": "1",
            "package_identifier": "findutils-1:4.6.0-20.el8.x86_64",
            "package_name": "findutils",
            "package_version": "4.6.0",
            "release": "20.el8",
            "src": False,
        },
    ]

    _EXAMPLE_PYTHON_PACKAGES_PRESENT = [
        {
            "location": "/usr/local/lib/python3.8/site-packages",
            "package_name": "pip",
            "package_version": "20.3.3",
        },
        {
            "location": "/usr/lib64/python3.6/site-packages",
            "package_name": "dbus-python",
            "package_version": "1.2.4",
        },
        {
            "location": "/usr/lib64/python3.6/site-packages",
            "package_name": "gpg",
            "package_version": "1.13.1",
        },
        {
            "location": "/usr/lib64/python3.6/site-packages",
            "package_name": "rpm",
            "package_version": "4.14.3",
        },
        {
            "location": "/usr/lib/python3.6/site-packages",
            "package_name": "requests",
            "package_version": "2.20.0",
        },
        {
            "location": "/opt/app-root/lib/python3.8/site-packages",
            "package_name": "wheel",
            "package_version": "0.36.2",
        },
        {
            "location": "/opt/app-root/lib/python3.8/site-packages",
            "package_name": "yarl",
            "package_version": "1.6.3",
        },
        {
            "location": "/opt/app-root/lib/python3.8/site-packages",
            "package_name": "yaspin",
            "package_version": "2.0.0",
        },
    ]

    def test_prepare_justification_link(self) -> None:
        """Test preparing links to justifications."""
        justification = [
            {"type": "INFO", "message": "Some info message", "link": "s2i_thoth"},
            {"type": "WARNING", "message": "Some warning message", "link": "https://thoth-station.ninja"},
            {"type": "ERROR", "message": "Some error message", "link": "https://thoth-station.ninja"},
        ]

        flexmock(UnitPrescription, run_prescription=justification)
        UnitPrescription._prepare_justification_link(justification)

        assert justification == [
            {"type": "INFO", "message": "Some info message", "link": jl("s2i_thoth")},
            {"type": "WARNING", "message": "Some warning message", "link": "https://thoth-station.ninja"},
            {"type": "ERROR", "message": "Some error message", "link": "https://thoth-station.ninja"},
        ]

    def test_should_include_dependencies(self, caplog, builder_context: PipelineBuilderContext) -> None:
        """Test including a pipeline unit based on dependencies."""
        assert builder_context.is_adviser_pipeline()

        should_include_dict = {"adviser_pipeline": True, "dependencies": {"boots": ["Foo"]}}
        PRESCRIPTION_UNIT_SHOULD_INCLUDE_SCHEMA(should_include_dict)
        UnitPrescription._PRESCRIPTION = {"name": "SomeUnitName", "should_include": should_include_dict}
        builder_context.should_receive("get_included_boot_names").and_yield("Foo")
        builder_context.should_receive("is_included").with_args(UnitPrescription).and_return(False)
        assert UnitPrescription._should_include_base(builder_context) is True

        should_include_dict = {"adviser_pipeline": True, "dependencies": {"boots": ["Foo"]}}
        PRESCRIPTION_UNIT_SHOULD_INCLUDE_SCHEMA(should_include_dict)
        UnitPrescription._PRESCRIPTION = {"name": "SomeUnitName", "should_include": should_include_dict}
        builder_context.should_receive("get_included_boot_names").and_yield()
        builder_context.should_receive("is_included").with_args(UnitPrescription).and_return(False)
        assert UnitPrescription._should_include_base(builder_context) is False

        should_include_dict = {
            "adviser_pipeline": True,
            "dependencies": {
                "boots": ["BootUnit1", "BootUnit2"],
                "pseudonyms": ["PseudonymUnit1"],
                "sieves": ["SieveUnit1"],
                "steps": ["StepUnit1"],
                "strides": ["StrideUnit1"],
                "wraps": ["WrapUnit1"],
            },
        }
        PRESCRIPTION_UNIT_SHOULD_INCLUDE_SCHEMA(should_include_dict)
        UnitPrescription._PRESCRIPTION = {"name": "SomeUnitName", "should_include": should_include_dict}
        builder_context.should_receive("get_included_boot_names").and_yield("BootUnit1", "BootUnit2")
        builder_context.should_receive("get_included_pseudonym_names").and_yield("PseudonymUnit1", "PseudonymUnit2")
        builder_context.should_receive("get_included_sieve_names").and_yield("SieveUnit1", "SieveUnit2")
        builder_context.should_receive("get_included_step_names").and_yield("StepUnit0", "StepUnit1")
        builder_context.should_receive("get_included_stride_names").and_yield("StrideUnit1")
        builder_context.should_receive("get_included_wrap_names").and_yield("WrapUnit1")
        builder_context.should_receive("is_included").with_args(UnitPrescription).and_return(False)
        assert UnitPrescription._should_include_base(builder_context) is True

    @pytest.mark.parametrize(
        "recommendation_type,allowed_recommendation_types,include",
        [
            (RecommendationType.LATEST, None, True),
            (RecommendationType.LATEST, ["latest"], True),
            (RecommendationType.STABLE, ["latest", "performance"], False),
            (RecommendationType.STABLE, ["latest", "performance", "stable"], True),
        ],
    )
    def test_should_include_recommendation_type(
        self,
        builder_context: PipelineBuilderContext,
        recommendation_type: RecommendationType,
        allowed_recommendation_types: Optional[List[str]],
        include: bool,
    ) -> None:
        """Test including a pipeline unit based on recommendation type."""
        should_include_dict = {"adviser_pipeline": True}
        if allowed_recommendation_types is not None:
            should_include_dict["recommendation_types"] = allowed_recommendation_types

        builder_context.recommendation_type = recommendation_type
        builder_context.decision_type = None

        assert builder_context.is_adviser_pipeline()
        PRESCRIPTION_UNIT_SHOULD_INCLUDE_SCHEMA(should_include_dict)
        UnitPrescription._PRESCRIPTION = {
            "name": "SomePrescriptionUnitName",
            "should_include": should_include_dict,
        }
        builder_context.should_receive("is_included").with_args(UnitPrescription).and_return(False).once()
        assert UnitPrescription._should_include_base(builder_context) == include

    @pytest.mark.parametrize(
        "authenticated,env_authenticated,include",
        [
            (True, True, True),
            (True, False, False),
            (False, False, True),
            (False, True, False),
            (None, False, True),
            (None, True, True),
        ],
    )
    def test_should_include_authentication(
        self,
        builder_context: PipelineBuilderContext,
        authenticated: Optional[bool],
        env_authenticated: bool,
        include: bool,
    ) -> None:
        """Test including a pipeline unit based on authentication."""
        should_include_dict = {"adviser_pipeline": True}
        if authenticated is not None:
            should_include_dict["authenticated"] = authenticated

        builder_context.recommendation_type = RecommendationType.LATEST
        builder_context.decision_type = None

        assert builder_context.is_adviser_pipeline()
        builder_context.authenticated = env_authenticated

        PRESCRIPTION_UNIT_SHOULD_INCLUDE_SCHEMA(should_include_dict)
        UnitPrescription._PRESCRIPTION = {
            "name": "SomePrescriptionUnitName",
            "should_include": should_include_dict,
        }
        builder_context.should_receive("is_included").with_args(UnitPrescription).and_return(False).once()
        assert UnitPrescription._should_include_base(builder_context) == include

    @pytest.mark.parametrize(
        "decision_type,allowed_decision_types,include",
        [
            (DecisionType.RANDOM, None, True),
            (DecisionType.RANDOM, ["random"], True),
            (DecisionType.ALL, ["random"], False),
            (DecisionType.ALL, ["random", "all"], True),
        ],
    )
    def test_should_include_decision_type(
        self,
        builder_context: PipelineBuilderContext,
        decision_type: DecisionType,
        allowed_decision_types: List[str],
        include: bool,
    ) -> None:
        """Test including a pipeline unit based on decision type."""
        should_include_dict = {"dependency_monkey_pipeline": True}
        if allowed_decision_types is not None:
            should_include_dict["decision_types"] = allowed_decision_types

        builder_context.recommendation_type = None
        builder_context.decision_type = decision_type

        assert builder_context.is_dependency_monkey_pipeline()
        PRESCRIPTION_UNIT_SHOULD_INCLUDE_SCHEMA(should_include_dict)
        UnitPrescription._PRESCRIPTION = {
            "name": "SomePrescriptionUnitName",
            "should_include": should_include_dict,
        }
        builder_context.should_receive("is_included").with_args(UnitPrescription).and_return(False).once()
        assert UnitPrescription._should_include_base(builder_context) == include

    def test_should_include_pipeline(self, builder_context: PipelineBuilderContext) -> None:
        """Test including based on pipeline type."""
        builder_context.recommendation_type = None
        builder_context.decision_type = DecisionType.ALL
        assert builder_context.is_dependency_monkey_pipeline()

        should_include_dict = {"dependency_monkey_pipeline": True}
        PRESCRIPTION_UNIT_SHOULD_INCLUDE_SCHEMA(should_include_dict)
        UnitPrescription._PRESCRIPTION = {
            "name": "SomePrescriptionUnitName",
            "should_include": should_include_dict,
        }
        builder_context.should_receive("is_included").with_args(UnitPrescription).and_return(False)
        # builder context has decision type ALL and prescription has dependency monkey pipeline configured
        assert UnitPrescription._should_include_base(builder_context) is True
        UnitPrescription.SHOULD_INCLUDE_CACHE.clear()

        builder_context.recommendation_type = RecommendationType.LATEST
        builder_context.decision_type = None
        assert builder_context.is_adviser_pipeline()

        # builder context has recommendation type LATEST and prescription has dependency monkey pipeline configured
        assert UnitPrescription._should_include_base(builder_context) is False
        UnitPrescription.SHOULD_INCLUDE_CACHE.clear()

        should_include_dict = {"adviser_pipeline": True}
        PRESCRIPTION_UNIT_SHOULD_INCLUDE_SCHEMA(should_include_dict)
        UnitPrescription._PRESCRIPTION = {
            "name": "SomePrescriptionUnitName",
            "should_include": should_include_dict,
        }
        builder_context.should_receive("is_included").with_args(UnitPrescription).and_return(False)
        # builder context has recommendation type LATEST and prescription has adviser pipeline configured
        assert UnitPrescription._should_include_base(builder_context) is True
        UnitPrescription.SHOULD_INCLUDE_CACHE.clear()

        builder_context.recommendation_type = None
        builder_context.decision_type = DecisionType.ALL
        assert builder_context.is_dependency_monkey_pipeline()

        # builder context has decision type ALL and prescription has adviser pipeline configured
        assert UnitPrescription._should_include_base(builder_context) is False
        UnitPrescription.SHOULD_INCLUDE_CACHE.clear()

    @pytest.mark.parametrize("adviser_pipeline", [True, False])
    def test_should_include_times(self, builder_context: PipelineBuilderContext, adviser_pipeline: bool) -> None:
        """Test including a pipeline unit based on `times`."""
        if adviser_pipeline:
            builder_context.recommendation_type = RecommendationType.LATEST
            builder_context.decision_type = None
            assert builder_context.is_adviser_pipeline()
            assert not builder_context.is_dependency_monkey_pipeline()
        else:
            builder_context.recommendation_type = None
            builder_context.decision_type = DecisionType.ALL
            assert builder_context.is_dependency_monkey_pipeline()
            assert not builder_context.is_adviser_pipeline()

        should_include_dict = {"times": 0, "adviser_pipeline": True, "dependency_monkey_pipeline": True}
        PRESCRIPTION_UNIT_SHOULD_INCLUDE_SCHEMA(should_include_dict)
        UnitPrescription._PRESCRIPTION = {
            "name": "Foo",
            "should_include": should_include_dict,
        }
        assert UnitPrescription._should_include_base(builder_context) is False

        builder_context.should_receive("is_included").with_args(UnitPrescription).and_return(False).and_return(
            True
        ).twice()

        should_include_dict = {"times": 1, "adviser_pipeline": True, "dependency_monkey_pipeline": True}
        PRESCRIPTION_UNIT_SHOULD_INCLUDE_SCHEMA(should_include_dict)
        UnitPrescription._PRESCRIPTION = {
            "name": "Foo",
            "should_include": should_include_dict,
        }
        assert UnitPrescription._should_include_base(builder_context) is True

        should_include_dict = {"times": 1, "adviser_pipeline": True, "dependency_monkey_pipeline": True}
        PRESCRIPTION_UNIT_SHOULD_INCLUDE_SCHEMA(should_include_dict)
        UnitPrescription._PRESCRIPTION = {
            "name": "Foo",
            "should_include": should_include_dict,
        }
        assert UnitPrescription._should_include_base(builder_context) is False

    @pytest.mark.parametrize(
        "prescription_runtime_environments,used_runtime_environment_dict,include",
        [
            # Python version.
            ({"python_version": ">=3.6,<=3.9"}, {"python_version": "3.6"}, True),
            ({"python_version": ">=3.6,<=3.9"}, {}, False),
            ({"python_version": "!=3.6,!=3.9"}, {}, False),
            ({"python_version": "==3.6"}, {"python_version": "3.9"}, False),
            ({"python_version": ">=0.0"}, {}, False),
            # Operating system.
            ({"operating_systems": [{"name": "rhel", "version": "8"}]}, {}, False),
            (
                {"operating_systems": [{"name": "rhel", "version": "8"}, {"name": "fedora", "version": "33"}]},
                {"operating_system": {"name": "fedora", "version": "8"}},
                False,
            ),
            (
                {"operating_systems": [{"name": "rhel", "version": "8"}, {"name": "fedora", "version": "33"}]},
                {"operating_system": {"name": "rhel", "version": "8"}},
                True,
            ),
            (
                {"operating_systems": [{"name": "rhel"}]},
                {"operating_system": {"name": "rhel", "version": "8"}},
                False,
            ),
            # CPU/GPU.
            (
                {"hardware": [{"cpu_flags": ["avx2"]}]},
                {"hardware": {"cpu_family": 9999, "cpu_model": 8888}},
                False,
            ),
            (
                {"hardware": [{"cpu_flags": ["avx2"]}]},
                {"hardware": {"cpu_family": 6, "cpu_model": int("0x5", base=16)}},
                True,
            ),
            (
                {"hardware": [{"cpu_flags": {"not": ["avx2"]}}]},
                {"hardware": {"cpu_family": 6, "cpu_model": int("0x5", base=16)}},
                False,
            ),
            (
                {"hardware": [{"cpu_flags": ["avx2", "avx512"], "cpu_families": [4, 5, 6], "cpu_models": [4, 5, 6]}]},
                {"hardware": {"cpu_family": 6, "cpu_model": int("0x5", base=16)}},
                True,
            ),
            (
                {
                    "hardware": [
                        {"cpu_flags": {"not": ["avx2", "avx512"]}, "cpu_families": [4, 5, 6], "cpu_models": [4, 5, 6]}
                    ]
                },
                {"hardware": {"cpu_family": 6, "cpu_model": int("0x5", base=16)}},
                False,
            ),
            (
                {"hardware": [{"cpu_families": [1, 2, 3], "cpu_models": [9, 8, 7], "gpu_models": [None, "Some"]}]},
                {"hardware": {"cpu_family": 1, "cpu_model": 7}},
                True,
            ),
            (
                {"hardware": [{"cpu_families": {"not": [1]}}]},
                {"hardware": {"cpu_family": 1}},
                False,
            ),
            (
                {"hardware": [{"cpu_models": {"not": [None]}}]},
                {"hardware": {"cpu_model": 1}},
                True,
            ),
            (
                {"hardware": [{"gpu_models": {"not": ["Bar"]}}]},
                {"hardware": {"gpu_model": "Foo"}},
                True,
            ),
            (
                {"hardware": [{"cpu_families": [1, 2, 3], "cpu_models": [9, 8, 7]}]},
                {"hardware": {"cpu_family": 2, "cpu_model": 6}},
                False,
            ),
            (
                {
                    "hardware": [
                        {"cpu_families": [1, 2, 3], "cpu_models": [9, 8, 7]},
                        {"cpu_families": [3], "cpu_models": [8, 7], "gpu_models": ["Some"]},
                    ]
                },
                {"hardware": {"cpu_family": 3, "cpu_model": 8, "gpu_model": "Some"}},
                True,
            ),
            # CUDA versions.
            ({"cuda_version": "<=9.0,>=8.1"}, {"cuda_version": "9.0"}, True),
            ({"cuda_version": "!=9.0,!=8.1"}, {"cuda_version": "9.0"}, False),
            ({"cuda_version": "<=9.0,>=8.1"}, {}, False),
            ({"cuda_version": "==8.1"}, {"cuda_version": "9.0"}, False),
            # platforms.
            ({"platforms": ["linux-x86_64", "linux-i586"]}, {"platform": "linux-x86_64"}, True),
            ({"platforms": ["linux-x86_64", "linux-i586"]}, {}, False),
            ({"platforms": ["linux-i586"]}, {"platform": "linux-x86_64"}, False),
            ({"platforms": ["linux-i586", None]}, {}, True),
            ({"platforms": {"not": ["linux-i586", None]}}, {}, False),
            # openblas_version.
            ({"openblas_version": "<=0.3.1,>=0.2.0"}, {"openblas_version": "0.3.1"}, True),
            ({"openblas_version": "<=0.3.1,>=0.2.0"}, {}, False),
            ({"openblas_version": "==0.2.0"}, {"openblas_version": "0.3.1"}, False),
            ({"openblas_version": "!=0.2.0"}, {}, False),
            # openmpi_version.
            ({"openmpi_version": "<=3.1,>=2.0"}, {"openmpi_version": "3.1"}, True),
            ({"openmpi_version": "<=3.1,>=2.0"}, {}, False),
            ({"openmpi_version": "==2.0"}, {"openmpi_version": "3.1"}, False),
            ({"openmpi_version": ">=0.0"}, {}, False),
            # cudnn_version.
            ({"cudnn_version": "<=8.1,>=8.0"}, {"cudnn_version": "8.1"}, True),
            ({"cudnn_version": "<=8.1,>=8.0"}, {}, False),
            ({"cudnn_version": "==8.0"}, {"cudnn_version": "8.1"}, False),
            ({"cudnn_version": "!=8.0"}, {}, False),
            # mkl_version.
            ({"mkl_version": "<=2021.1.1,>=2019.0"}, {"mkl_version": "2021.1.1"}, True),
            ({"mkl_version": "<=2021.1.1,>=2019.0"}, {}, False),
            ({"mkl_version": "==2019.0"}, {"mkl_version": "2021.1.1"}, False),
            ({"mkl_version": "!=2019.0"}, {"mkl_version": "2021.1.1"}, True),
            # base images.
            (
                {
                    "base_images": [
                        "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0",
                        "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0",
                    ]
                },
                {"base_image": "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0"},
                True,
            ),
            (
                {
                    "base_images": [
                        "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0",
                        "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0",
                    ]
                },
                {},
                False,
            ),
            (
                {"base_images": ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0"]},
                {"base_image": "quay.io/thoth-station/s2i-thoth-ubi8-py38:v1.0.0"},
                False,
            ),
            ({"base_images": ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0", None]}, {}, True),
            (
                {"base_images": {"not": ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0"]}},
                {"base_image": "quay.io/thoth-station/s2i-thoth-ubi8-py38:v1.0.0"},
                True,
            ),
            (
                {
                    "base_images": {
                        "not": [
                            "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0",
                            "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0",
                        ]
                    }
                },
                {},
                True,
            ),
            # Configuration combination.
            (
                {
                    "python_version": ">=3.6,<=3.9",
                    "cuda_version": "==9.0",
                    "cudnn_version": "<=3.1,>=3.0",
                    "base_images": [None, "quay.io/thoth-station/s2i-thoth-ubi8-py38:v1.0.0"],
                    "platforms": ["linux-x86_64"],
                    "operating_systems": [{"name": "rhel", "version": "8.0"}, {"name": "fedora", "version": "30"}],
                    "hardware": [{"cpu_families": [1, 2, 3], "cpu_models": [9, 8, 7], "gpu_models": [None, "Some"]}],
                },
                {
                    "python_version": "3.6",
                    "cuda_version": "9.0",
                    "cudnn_version": "3.1",
                    "base_image": "quay.io/thoth-station/s2i-thoth-ubi8-py38:v1.0.0",
                    "platform": "linux-x86_64",
                    "operating_system": {"name": "rhel", "version": "8.0"},
                    "hardware": {"cpu_family": 1, "cpu_model": 7},
                },
                True,
            ),
            (
                {
                    "python_version": ">=3.6,<=3.9",
                    "cuda_version": "==9.0",
                    "cudnn_version": "<=3.1,>=3.0",
                    "base_images": [None, "quay.io/thoth-station/s2i-thoth-ubi8-py38:v1.0.0"],
                    "platforms": ["linux-x86_64"],
                    "operating_systems": [{"name": "rhel", "version": "8.0"}, {"name": "fedora", "version": "30"}],
                    "hardware": [
                        # CPU model does not match.
                        {"cpu_families": [1, 2, 3], "cpu_models": [9, 8], "gpu_models": [None, "Some"]}
                    ],
                },
                {
                    "python_version": "3.6",
                    "cuda_version": "9.0",
                    "cudnn_version": "3.1",
                    "base_image": "quay.io/thoth-station/s2i-thoth-ubi8-py38:v1.0.0",
                    "platform": "linux-x86_64",
                    "operating_system": {"name": "rhel", "version": "8.0"},
                    "hardware": {"cpu_family": 1, "cpu_model": 7},
                },
                False,
            ),
        ],
    )
    def test_should_include_runtime_environment(
        self,
        builder_context: PipelineBuilderContext,
        prescription_runtime_environments: Dict[str, Any],
        used_runtime_environment_dict: Dict[str, Any],
        include: bool,
    ) -> None:
        """Test parsing and including the given should include entry."""
        PRESCRIPTION_UNIT_SHOULD_INCLUDE_RUNTIME_ENVIRONMENTS_SCHEMA(prescription_runtime_environments)
        builder_context.project.runtime_environment = RuntimeEnvironment.from_dict(used_runtime_environment_dict)
        UnitPrescription._PRESCRIPTION = {
            "name": "Bar",
            "should_include": {
                "adviser_pipeline": True,
                "runtime_environments": prescription_runtime_environments,
            },
        }
        builder_context.should_receive("is_included").with_args(UnitPrescription).and_return(False).once()

        assert builder_context.is_adviser_pipeline()
        assert UnitPrescription._should_include_base(builder_context) == include

    @pytest.mark.parametrize(
        "prescription_base_images,used_base_image,include",
        [
            ([None], None, True),
            (["quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0"], None, False),
            ([None], "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0", False),
            (
                ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0"],
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0",
                True,
            ),
            # No tag specified in the prescription.
            (["quay.io/thoth-station/s2i-thoth-ubi8-py36"], "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0", True),
            # Tag for any specified.
            (["quay.io/thoth-station/s2i-thoth-ubi8-py36:*"], "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0", True),
            # Matching desired releases.
            (
                ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0*"],
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0",
                True,
            ),
            (
                ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.*"],
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0",
                True,
            ),
            (
                ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0*"],
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0",
                True,
            ),
            (
                ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.*"],
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0",
                True,
            ),
            (
                ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v1*"],
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0",
                True,
            ),
            (
                ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v*"],
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0",
                True,
            ),
            # Not matching tag.
            (
                ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0"],
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.1",
                False,
            ),
            (
                ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0*"],
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.1",
                False,
            ),
            (
                ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.*"],
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.1.0",
                False,
            ),
            (
                ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.*"],
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v2.0",
                False,
            ),
            (
                ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v1*"],
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v2.0",
                False,
            ),
            # Not matching image.
            (
                ["quay.io/thoth-station/s2i-thoth-ubi8-py39:v1.0"],
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0",
                False,
            ),
            (
                ["quay.io/thoth-station/s2i-thoth-ubi8-py39:v1.*"],
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0",
                False,
            ),
            #
            # Inverted matching.
            #
            ({"not": [None]}, None, False),
            ({"not": ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0"]}, None, True),
            ({"not": [None]}, "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0", True),
            (
                {"not": ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0"]},
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0",
                False,
            ),
            # No tag specified in the prescription.
            (
                {"not": ["quay.io/thoth-station/s2i-thoth-ubi8-py36"]},
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0",
                False,
            ),
            # Tag for any specified.
            (
                {"not": ["quay.io/thoth-station/s2i-thoth-ubi8-py36:*"]},
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0",
                False,
            ),
            # Matching desired releases.
            (
                {"not": ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0*"]},
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0",
                False,
            ),
            (
                {"not": ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.*"]},
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0",
                False,
            ),
            (
                {"not": ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0*"]},
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0",
                False,
            ),
            (
                {"not": ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.*"]},
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0",
                False,
            ),
            (
                {"not": ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v1*"]},
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0",
                False,
            ),
            (
                {"not": ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v*"]},
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0",
                False,
            ),
            # Not matching tag.
            (
                {"not": ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0"]},
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.1",
                True,
            ),
            (
                {"not": ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0*"]},
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.1",
                True,
            ),
            (
                {"not": ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.*"]},
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.1.0",
                True,
            ),
            (
                {"not": ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.*"]},
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v2.0",
                True,
            ),
            (
                {"not": ["quay.io/thoth-station/s2i-thoth-ubi8-py36:v1*"]},
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v2.0",
                True,
            ),
            # Not matching image.
            (
                {"not": ["quay.io/thoth-station/s2i-thoth-ubi8-py39:v1.0"]},
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0",
                True,
            ),
            (
                {"not": ["quay.io/thoth-station/s2i-thoth-ubi8-py39:v1.*"]},
                "quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0",
                True,
            ),
        ],
    )
    def test_should_include_base_images(
        self,
        builder_context: PipelineBuilderContext,
        prescription_base_images: Union[List[Optional[str]], Dict[str, List[Optional[str]]]],
        used_base_image: Optional[str],
        include: bool,
    ) -> None:
        """Test more sophisticated expressions specifying inclusion base on base images."""
        UnitPrescription._PRESCRIPTION = {
            "name": "FooBarName",
            "should_include": {
                "adviser_pipeline": True,
                "runtime_environments": {
                    "base_images": prescription_base_images,
                },
            },
        }
        PRESCRIPTION_UNIT_SHOULD_INCLUDE_SCHEMA(UnitPrescription._PRESCRIPTION["should_include"])
        builder_context.project.runtime_environment.base_image = used_base_image

        builder_context.should_receive("is_included").with_args(UnitPrescription).and_return(False).once()

        assert builder_context.is_adviser_pipeline()
        assert UnitPrescription._should_include_base(builder_context) == include

    @pytest.mark.parametrize(
        "library_usage_expected,library_usage_supplied,include",
        [
            ({"tensorflow": ["tensorflow.keras.layers.Embedding"]}, None, False),
            (None, {"tensorflow": ["tensorflow.keras.layers.Embedding"]}, True),
            ({"tensorflow": ["tensorflow.keras.layers.Embedding"]}, {"flask": ["flask.Flask"]}, False),
            (
                {"tensorflow": ["tensorflow.keras.layers.Embedding", "tensorflow.Graph"]},
                {"tensorflow": ["tensorflow.Assert"]},
                False,
            ),
            ({"flask": ["flask.Flask"]}, {"tensorflow": ["tensorflow.keras.layers.Embedding"]}, False),
            ({"flask": ["flask.*"]}, {"flask": ["flask.Flask"]}, True),
            (
                {"flask": ["flask.*"]},
                {"tensorflow": ["tensorflow.keras.layers.Embedding"], "flask": ["flask.Flask"]},
                True,
            ),
            (
                {"flask": ["flask.*"], "tensorflow": ["tensorflow.*"]},
                {"flask": ["flask.Flask"], "tensorflow": ["tensorflow.keras.layers.Embedding"]},
                True,
            ),
        ],
    )
    def test_should_include_library_usage(
        self,
        builder_context: PipelineBuilderContext,
        library_usage_expected: Optional[Dict[str, Any]],
        library_usage_supplied: Optional[Dict[str, Any]],
        include: bool,
    ) -> None:
        """Test checking library usage."""
        should_include = {"adviser_pipeline": True}
        if library_usage_expected is not None:
            should_include["library_usage"] = library_usage_expected

        PRESCRIPTION_UNIT_SHOULD_INCLUDE_SCHEMA(should_include)

        UnitPrescription._PRESCRIPTION = {
            "name": "LibraryUsageUnit",
            "should_include": should_include,
        }

        builder_context.library_usage = library_usage_supplied
        builder_context.recommendation_type = RecommendationType.LATEST
        builder_context.decision_type = None
        assert builder_context.is_adviser_pipeline()
        builder_context.should_receive("is_included").with_args(UnitPrescription).and_return(False).once()
        assert UnitPrescription._should_include_base(builder_context) == include

    @pytest.mark.parametrize(
        "labels_expected,labels_supplied,include",
        [
            ({}, {}, True),
            ({"foo": "bar"}, {}, False),
            ({}, {"foo": "bar"}, True),
            ({"foo": "bar"}, {"foo": "bar"}, True),
            ({"foo": "bar", "qux": "baz"}, {"foo": "bar"}, True),
            ({"foo": "bar"}, {"foo": "bar", "qux": "baz"}, True),
            ({"foo": "bar"}, {"qux": "baz", "baz": "foo"}, False),
        ],
    )
    def test_should_include_labels(
        self,
        builder_context: PipelineBuilderContext,
        labels_expected: Optional[Dict[str, str]],
        labels_supplied: Dict[str, str],
        include: bool,
    ) -> None:
        """Test including pipeline units based on labels."""
        should_include = {"adviser_pipeline": True}
        if labels_expected is not None:
            should_include["labels"] = labels_expected

        PRESCRIPTION_UNIT_SHOULD_INCLUDE_SCHEMA(should_include)

        UnitPrescription._PRESCRIPTION = {
            "name": "LabelsUnit",
            "should_include": should_include,
        }

        builder_context.recommendation_type = RecommendationType.LATEST
        builder_context.decision_type = None
        builder_context.labels = labels_supplied
        assert builder_context.is_adviser_pipeline()
        builder_context.should_receive("is_included").with_args(UnitPrescription).and_return(False).once()
        assert UnitPrescription._should_include_base(builder_context) == include

    @pytest.mark.parametrize(
        "abi_present,abi_configured,include",
        [
            ([], [], True),
            (["GLIBC_2.2.5"], [], True),
            ([], ["GLIBC_2.2.5"], False),
            (["GLIBC_2.2.5"], ["GLIBC_2.2.5"], True),
            (["GLIBC_2.2.5", "GNUTLS_3_6_14"], ["GLIBC_2.2.5"], True),
            (["GLIBC_2.2.5"], ["GNUTLS_3_6_14", "GLIBC_2.2.5"], False),
            (["GLIBC_2.2.5", "GNUTLS_3_6_14"], ["GNUTLS_3_6_14", "GLIBC_2.2.5"], True),
            (["GLIBC_2.2.5", "GNUTLS_3_6_14"], {"not": ["GNUTLS_3_6_14"]}, False),
            (["GLIBC_2.2.5"], {"not": ["GNUTLS_3_6_14"]}, True),
            (["GNUTLS_3_6_14"], {"not": ["GLIBC_2.2.5", "GNUTLS_3_6_14"]}, False),
            ([], {"not": ["GLIBC_2.2.5"]}, False),
        ],
    )
    def test_should_include_abi(
        self,
        builder_context: PipelineBuilderContext,
        abi_present: Optional[List[str]],
        abi_configured: Union[List[str], Dict[str, List[str]]],
        include: bool,
    ) -> None:
        """Test including pipeline units based on ABI present in the base image."""
        base_image_present_name, base_image_present_version = "s2i-thoth", "1.0.0"
        builder_context.project.runtime_environment.base_image = (
            f"{base_image_present_name}:v{base_image_present_version}"
        )
        should_include = {
            "adviser_pipeline": True,
            "runtime_environments": {"base_images": [builder_context.project.runtime_environment.base_image]},
        }

        if abi_configured:
            should_include["runtime_environments"]["abi"] = abi_configured

        PRESCRIPTION_UNIT_SHOULD_INCLUDE_SCHEMA(should_include)

        if abi_configured:
            builder_context.graph.should_receive("get_thoth_s2i_analyzed_image_symbols_all").with_args(
                base_image_present_name,
                base_image_present_version,
                is_external=False,
            ).and_return(abi_present).once()
        else:
            builder_context.graph.should_receive("get_thoth_s2i_analyzed_image_symbols_all").times(0)

        UnitPrescription._PRESCRIPTION = {
            "name": "SharedObjectsUnit",
            "should_include": should_include,
        }

        builder_context.recommendation_type = RecommendationType.LATEST
        builder_context.decision_type = None

        assert builder_context.is_adviser_pipeline()
        builder_context.should_receive("is_included").with_args(UnitPrescription).and_return(False).once()
        assert UnitPrescription._should_include_base(builder_context) == include

    @pytest.mark.parametrize("base_images", [[], ["s2i-thoth:v1.0.0"], ["s2i-thoth:v1.0.0", "s2i-thoth:v2.0.0"]])
    def test_should_include_abi_no_image_error(
        self, base_images: List[str], builder_context: PipelineBuilderContext
    ) -> None:
        """Test including pipeline units based on ABI present in the base image.

        This test covers a case when base image is not present in the user's configuration file.
        """
        builder_context.project.runtime_environment.base_image = None
        should_include = {
            "adviser_pipeline": True,
            "runtime_environments": {
                "abi": ["GNUTLS_3_6_14"],
            },
        }

        if base_images:
            should_include["runtime_environments"]["base_images"] = base_images

        PRESCRIPTION_UNIT_SHOULD_INCLUDE_SCHEMA(should_include)

        UnitPrescription._PRESCRIPTION = {
            "name": "SharedObjectsUnit",
            "should_include": should_include,
        }

        builder_context.recommendation_type = RecommendationType.LATEST
        builder_context.decision_type = None

        assert builder_context.is_adviser_pipeline()
        builder_context.should_receive("is_included").with_args(UnitPrescription).and_return(False).once()
        assert UnitPrescription._should_include_base(builder_context) is False

    @pytest.mark.parametrize(
        "rpms_present,rpms_configured,include",
        [
            ([], [], True),
            ([{"package_name": "git"}], [], True),
            ([], [{"package_name": "git"}], False),
            ([{"package_name": "git"}], [{"package_name": "git"}], True),
            ([{"package_name": "git"}], [{"package_name": "git"}], True),
            ([{"package_name": "git"}, {"package_name": "glibc"}], [{"package_name": "git"}], True),
            (
                _EXAMPLE_RPM_PACKAGES_PRESENT,
                [
                    {
                        "arch": "x86_64",
                        "package_name": "gcc",
                        "package_version": "8.3.1",
                        "release": "5.1.el8",
                    },
                    {
                        "epoch": "1",
                        "package_name": "findutils",
                        "package_version": "4.6.0",
                        "release": "20.el8",
                        "src": False,
                    },
                ],
                True,
            ),
            (
                _EXAMPLE_RPM_PACKAGES_PRESENT,
                [
                    {
                        "arch": "x86_64",
                        "package_name": "gcc",
                        "package_version": "8.3.1",
                        "release": "5.1.el8",
                    },
                    {
                        "epoch": "1",
                        "package_name": "findutils",
                        "package_version": "5.0.0",  # This version is not present.
                        "release": "20.el8",
                        "src": False,
                    },
                ],
                False,
            ),
            (
                _EXAMPLE_RPM_PACKAGES_PRESENT,
                {
                    "not": [
                        {
                            "arch": "x86_64",
                            "package_name": "gcc",
                            "package_version": "8.3.1",
                            "release": "5.1.el8",
                        },
                        {
                            "epoch": "1",
                            "package_name": "findutils",
                            "package_version": "5.0.0",  # This version is not present.
                            "release": "20.el8",
                            "src": False,
                        },
                    ]
                },
                True,
            ),
            (
                _EXAMPLE_RPM_PACKAGES_PRESENT,
                {
                    "not": [
                        {
                            "arch": "x86_64",
                            "package_name": "gcc",
                            "package_version": "8.3.1",
                            "release": "5.1.el8",
                        },
                        {
                            "epoch": "1",
                            "package_name": "findutils",
                            "package_version": "4.6.0",
                            "release": "20.el8",
                            "src": False,
                        },
                    ]
                },
                False,
            ),
        ],
    )
    def test_should_include_rpm_packages(
        self,
        builder_context: PipelineBuilderContext,
        rpms_present: List[Dict[str, str]],
        rpms_configured: List[Dict[str, str]],
        include: bool,
    ) -> None:
        """Test including pipeline units based on RPM packages present in the base image."""
        base_image_present_name, base_image_present_version = "s2i-thoth", "1.0.0"
        builder_context.project.runtime_environment.base_image = (
            f"{base_image_present_name}:v{base_image_present_version}"
        )
        should_include = {
            "adviser_pipeline": True,
            "runtime_environments": {"base_images": [builder_context.project.runtime_environment.base_image]},
        }

        if rpms_configured:
            should_include["runtime_environments"]["rpm_packages"] = rpms_configured

        PRESCRIPTION_UNIT_SHOULD_INCLUDE_SCHEMA(should_include)

        if rpms_configured:
            builder_context.graph.should_receive("get_last_analysis_document_id").with_args(
                base_image_present_name,
                base_image_present_version,
                is_external=False,
            ).and_return("package-extract-foo-bar").once()
            builder_context.graph.should_receive("get_rpm_package_version_all").with_args(
                "package-extract-foo-bar"
            ).and_return(rpms_present).once()
        else:
            builder_context.graph.should_receive("get_last_analysis_document_id").times(0)
            builder_context.graph.should_receive("get_rpm_package_version_all").times(0)

        UnitPrescription._PRESCRIPTION = {
            "name": "RPMPackagesUnit",
            "should_include": should_include,
        }

        builder_context.recommendation_type = RecommendationType.LATEST
        builder_context.decision_type = None

        assert builder_context.is_adviser_pipeline()
        builder_context.should_receive("is_included").with_args(UnitPrescription).and_return(False).once()
        assert UnitPrescription._should_include_base(builder_context) == include

    @pytest.mark.parametrize("base_images", [[], ["s2i-thoth:v1.0.0"], ["s2i-thoth:v1.0.0", "s2i-thoth:v2.0.0"]])
    def test_should_include_rpm_packages_no_image_error(
        self,
        builder_context: PipelineBuilderContext,
        base_images: List[str],
    ) -> None:
        """Test including pipeline units based on RPM packages present in the base image.

        This test covers a case when base image is not present in the user's configuration file.
        """
        builder_context.project.runtime_environment.base_image = None
        should_include = {
            "adviser_pipeline": True,
            "runtime_environments": {
                "rpm_packages": [
                    {
                        "package_name": "git",
                    }
                ],
            },
        }

        if base_images:
            should_include["runtime_environments"]["base_images"] = base_images

        PRESCRIPTION_UNIT_SHOULD_INCLUDE_SCHEMA(should_include)

        UnitPrescription._PRESCRIPTION = {
            "name": "RPMPackagesUnit",
            "should_include": should_include,
        }

        builder_context.recommendation_type = RecommendationType.LATEST
        builder_context.decision_type = None

        assert builder_context.is_adviser_pipeline()
        builder_context.should_receive("is_included").with_args(UnitPrescription).and_return(False).once()
        assert UnitPrescription._should_include_base(builder_context) is False

    def test_should_include_rpm_packages_no_analysis(self, builder_context: PipelineBuilderContext) -> None:
        """Test not including pipeline units if the base image was not analysed."""
        base_image_present_name, base_image_present_version = "s2i-thoth", "1.0.0"
        builder_context.project.runtime_environment.base_image = (
            f"{base_image_present_name}:v{base_image_present_version}"
        )
        should_include = {
            "adviser_pipeline": True,
            "runtime_environments": {
                "base_images": [builder_context.project.runtime_environment.base_image],
                "rpm_packages": [{"package_name": "glibc"}],
            },
        }

        PRESCRIPTION_UNIT_SHOULD_INCLUDE_SCHEMA(should_include)

        builder_context.graph.should_receive("get_last_analysis_document_id").with_args(
            base_image_present_name,
            base_image_present_version,
            is_external=False,
        ).and_return(None).once()
        builder_context.graph.should_receive("get_rpm_package_version_all").times(0)

        UnitPrescription._PRESCRIPTION = {
            "name": "RPMPackagesUnit",
            "should_include": should_include,
        }

        builder_context.recommendation_type = RecommendationType.LATEST
        builder_context.decision_type = None

        assert builder_context.is_adviser_pipeline()
        builder_context.should_receive("is_included").with_args(UnitPrescription).and_return(False).once()
        assert UnitPrescription._should_include_base(builder_context) is False

    @pytest.mark.parametrize(
        "python_present,python_configured,include",
        [
            ([], [], True),
            (_EXAMPLE_PYTHON_PACKAGES_PRESENT, [], True),
            # # Present.
            (_EXAMPLE_PYTHON_PACKAGES_PRESENT, [{"name": "dbus-python"}], True),
            (_EXAMPLE_PYTHON_PACKAGES_PRESENT, [{"name": "dbus-python"}, {"name": "wheel"}], True),
            (_EXAMPLE_PYTHON_PACKAGES_PRESENT, [{"name": "dbus-python", "version": "<1.3.0,>1.2.0"}], True),
            (
                _EXAMPLE_PYTHON_PACKAGES_PRESENT,
                [{"name": "dbus-python", "version": "<1.3.0,>1.2.0"}, {"name": "wheel", "version": "~=0.36.0"}],
                True,
            ),
            (
                _EXAMPLE_PYTHON_PACKAGES_PRESENT,
                [
                    {"name": "dbus-python", "version": "<1.3.0,>1.2.0", "location": "^/usr/lib64/.*"},
                    {"name": "wheel", "version": "<=0.40.0", "location": "^/opt/app-root/lib/python3.8/site-packages$"},
                ],
                True,
            ),
            (_EXAMPLE_PYTHON_PACKAGES_PRESENT, [{"name": "micropipenv"}], False),  # Not present.
            # Present but different version.
            (_EXAMPLE_PYTHON_PACKAGES_PRESENT, [{"name": "dbus-python", "version": ">=2.0.0"}], False),
            (
                _EXAMPLE_PYTHON_PACKAGES_PRESENT,
                [{"name": "dbus-python", "version": "<1.3.0,>1.2.0"}, {"name": "wheel", "version": "==0.36.0"}],
                False,
            ),
            # Present but in another location.
            (
                _EXAMPLE_PYTHON_PACKAGES_PRESENT,
                [
                    {"name": "dbus-python", "version": "<1.3.0,>1.2.0", "location": "^/usr/lib64/"},
                    {"name": "wheel", "version": "<=0.40.0", "location": "^/home/thoth$"},
                ],
                False,
            ),
            # Not present.
            ([], [{"name": "micropipenv"}], False),
            # Test "not" logic.
            # micropipenv is not present.
            (_EXAMPLE_PYTHON_PACKAGES_PRESENT, {"not": [{"name": "micropipenv"}]}, True),
            # All not present.
            (_EXAMPLE_PYTHON_PACKAGES_PRESENT, {"not": [{"name": "micropipenv"}, {"name": "selinon"}]}, True),
            # dbus-python present.
            (_EXAMPLE_PYTHON_PACKAGES_PRESENT, {"not": [{"name": "dbus-python"}, {"name": "selinon"}]}, False),
            # dbus-python present in different location, selinon not present
            (
                _EXAMPLE_PYTHON_PACKAGES_PRESENT,
                {
                    "not": [
                        {"name": "selinon"},
                        {"name": "dbus-python", "location": "^/home/thoth/.*"},
                    ]
                },
                True,
            ),
            # Version does not match so should be included based on "not".
            (
                _EXAMPLE_PYTHON_PACKAGES_PRESENT,
                {
                    "not": [
                        {"name": "dbus-python", "version": ">=2.0"},
                    ],
                },
                True,
            ),
        ],
    )
    def test_should_include_python_packages(
        self,
        builder_context: PipelineBuilderContext,
        python_present: List[Dict[str, str]],
        python_configured: List[Dict[str, str]],
        include: bool,
    ) -> None:
        """Test including pipeline units based on RPM packages present in the base image."""
        base_image_present_name, base_image_present_version = "s2i-thoth", "1.0.0"
        builder_context.project.runtime_environment.base_image = (
            f"{base_image_present_name}:v{base_image_present_version}"
        )
        should_include = {
            "adviser_pipeline": True,
            "runtime_environments": {"base_images": [builder_context.project.runtime_environment.base_image]},
        }

        if python_configured:
            should_include["runtime_environments"]["python_packages"] = python_configured

        PRESCRIPTION_UNIT_SHOULD_INCLUDE_SCHEMA(should_include)

        if python_configured:
            builder_context.graph.should_receive("get_last_analysis_document_id").with_args(
                base_image_present_name,
                base_image_present_version,
                is_external=False,
            ).and_return("package-extract-foo-bar").once()
            builder_context.graph.should_receive("get_python_package_version_all").with_args(
                "package-extract-foo-bar"
            ).and_return(python_present).once()
        else:
            builder_context.graph.should_receive("get_last_analysis_document_id").times(0)
            builder_context.graph.should_receive("get_rpm_package_version_all").times(0)

        UnitPrescription._PRESCRIPTION = {
            "name": "PythonPackagesUnit",
            "should_include": should_include,
        }

        builder_context.recommendation_type = RecommendationType.LATEST
        builder_context.decision_type = None

        assert builder_context.is_adviser_pipeline()
        builder_context.should_receive("is_included").with_args(UnitPrescription).and_return(False).once()
        assert UnitPrescription._should_include_base(builder_context) == include

    @pytest.mark.parametrize("base_images", [[], ["s2i-thoth:v1.0.0"], ["s2i-thoth:v1.0.0", "s2i-thoth:v2.0.0"]])
    def test_should_include_python_packages_no_image_error(
        self,
        builder_context: PipelineBuilderContext,
        base_images: List[str],
    ) -> None:
        """Test including pipeline units based on Python packages present in the base image.

        This test covers a case when base image is not present in the user's configuration file.
        """
        builder_context.project.runtime_environment.base_image = None
        should_include = {
            "adviser_pipeline": True,
            "runtime_environments": {
                "python_packages": [
                    {
                        "name": "dbus-python",
                    }
                ],
            },
        }

        if base_images:
            should_include["runtime_environments"]["base_images"] = base_images

        PRESCRIPTION_UNIT_SHOULD_INCLUDE_SCHEMA(should_include)

        UnitPrescription._PRESCRIPTION = {
            "name": "PythonPackagesUnit",
            "should_include": should_include,
        }

        builder_context.recommendation_type = RecommendationType.LATEST
        builder_context.decision_type = None

        assert builder_context.is_adviser_pipeline()
        builder_context.should_receive("is_included").with_args(UnitPrescription).and_return(False).once()
        assert UnitPrescription._should_include_base(builder_context) is False

    def test_should_include_python_packages_no_analysis(self, builder_context: PipelineBuilderContext) -> None:
        """Test not including pipeline units if the base image was not analyzed."""
        base_image_present_name, base_image_present_version = "s2i-thoth", "1.0.0"
        builder_context.project.runtime_environment.base_image = (
            f"{base_image_present_name}:v{base_image_present_version}"
        )
        should_include = {
            "adviser_pipeline": True,
            "runtime_environments": {
                "base_images": [builder_context.project.runtime_environment.base_image],
                "python_packages": [{"name": "dbus-python"}],
            },
        }

        PRESCRIPTION_UNIT_SHOULD_INCLUDE_SCHEMA(should_include)

        builder_context.graph.should_receive("get_last_analysis_document_id").with_args(
            base_image_present_name,
            base_image_present_version,
            is_external=False,
        ).and_return(None).once()
        builder_context.graph.should_receive("get_python_package_version_all").times(0)

        UnitPrescription._PRESCRIPTION = {
            "name": "PythonPackagesUnit",
            "should_include": should_include,
        }

        builder_context.recommendation_type = RecommendationType.LATEST
        builder_context.decision_type = None

        assert builder_context.is_adviser_pipeline()
        builder_context.should_receive("is_included").with_args(UnitPrescription).and_return(False).once()
        assert UnitPrescription._should_include_base(builder_context) is False
