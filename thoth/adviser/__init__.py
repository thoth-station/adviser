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

"""Thoth's adviser for recommending Python stacks."""

from .beam import Beam
from .boot import Boot
from .context import Context
from .dependency_monkey import DependencyMonkey
from .dm_report import DependencyMonkeyReport
from .enums import DecisionType
from .enums import Ecosystem
from .enums import PythonRecommendationOutput
from .enums import RecommendationType
from .pipeline_builder import PipelineBuilder
from .pipeline_config import PipelineConfig
from .predictor import Predictor
from .product import Product
from .report import Report
from .resolver import Resolver
from .sieve import Sieve
from .state import State
from .step import Step
from .stride import Stride
from .unit import Unit
from .wrap import Wrap

__title__ = "thoth-adviser"
__version__ = "0.9.4"
__author__ = "Fridolin Pokorny <fridolin@redhat.com>"


__all__ = [
    "Beam",
    "Boot",
    "Context",
    "DecisionType",
    "DependencyMonkey",
    "DependencyMonkeyReport",
    "Ecosystem",
    "PipelineBuilder",
    "PipelineConfig",
    "Predictor",
    "Product",
    "PythonRecommendationOutput",
    "RecommendationType",
    "Report",
    "Resolver",
    "Sieve",
    "State",
    "Step",
    "Stride",
    "__title__",
    "Unit",
    "__version__",
    "Wrap",
]
