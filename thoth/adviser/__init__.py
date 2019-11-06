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

"""Thoth's adviser for recommending Python stacks."""

from .anneal import AdaptiveSimulatedAnnealing
from .beam import Beam
from .enums import DecisionType
from .enums import Ecosystem
from .enums import PythonRecommendationOutput
from .enums import RecommendationType
from .pipeline_builder import PipelineBuilder
from .pipeline_config import PipelineConfig
from .product import Product
from .report import Report
from .temperature import ASATemperatureFunction

__title__ = "thoth-adviser"
__version__ = "0.6.2"
__author__ = "Fridolin Pokorny <fridolin@redhat.com>"


__all__ = [
    "AdaptiveSimulatedAnnealing",
    "ASATemperatureFunction",
    "Beam",
    "DecisionType",
    "Ecosystem",
    "PipelineBuilder",
    "PipelineConfig",
    "Product",
    "PythonRecommendationOutput",
    "RecommendationType",
    "Report",
    "__title__",
    "__version__",
]
