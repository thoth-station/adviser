#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2018, 2019 Fridolin Pokorny
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

"""Routines for dependency monkey and its output handling."""

import os
import sys
import json
import logging
from typing import Any
from typing import Dict
from typing import Optional
from typing import List
from typing import Tuple
from functools import partial

import attr
import matplotlib
from amun import inspect as amun_inspect
from thoth.python import Project

from .anneal import AdaptiveSimulatedAnnealing
from .enums import DecisionType
from .plot import plot_history


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class DependencyMonkeyReport:
    """Report produced by a Dependency Monkey run."""

    _skipped = attr.ib(type=int, default=0)
    _responses = attr.ib(type=List[str], default=attr.Factory(list))
    _temperature_history = attr.ib(
        type=Optional[List[Tuple[float, bool, float, int]]], default=None
    )

    def inc_skipped(self) -> None:
        """Increment skipped stacks (e.g. due to API unavailability errors)."""
        self._skipped += 1

    def set_temperature_history(
        self, temperature_history: List[Tuple[float, bool, float, int]]
    ) -> None:
        """Mark the temperature history during annealing."""
        self._temperature_history = temperature_history

    def add_response(self, response: str) -> None:
        """Add a new response to response listing."""
        self._responses.append(response)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to a dict representation suitable for serialization."""
        return {"skipped": self._skipped, "responses": self._responses}

    def plot_history(
        self, output_file: Optional[str] = None
    ) -> matplotlib.figure.Figure:
        """Plot history of temperature function."""
        return plot_history(self._temperature_history, output_file)


@attr.s(slots=True)
class DependencyMonkey:
    """Dependency monkey creates stacks based on the configuration using ASA."""

    asa = attr.ib(type=AdaptiveSimulatedAnnealing, kw_only=True)
    stack_output = attr.ib(type=str, kw_only=True, default="-")
    context = attr.ib(
        type=Optional[Dict[Any, Any]], default=attr.Factory(dict), kw_only=True
    )
    dry_run = attr.ib(type=bool, default=False, kw_only=True)
    decision_type = attr.ib(type=DecisionType, default=DecisionType.ALL, kw_only=True)

    def anneal(self, *, with_devel: bool = True) -> DependencyMonkeyReport:
        """Perform simulated annealing and run dependency monkey on products."""
        if self.stack_output == "-":
            _LOGGER.debug(
                "Results of Dependency Monkey run will be printed to standard output"
            )
            output_func = self._dm_stdout_output
        elif self.stack_output.startswith(("https://", "http://")):
            _LOGGER.debug(
                "Results of Dependency Monkey run will be submitted to API endpoint %r",
                self.stack_output,
            )
            output_func = partial(  # type: ignore
                self._dm_amun_output, self.stack_output, self.context
            )
        else:
            _LOGGER.debug(
                "Results of Dependency Monkey run will be stored in directory %r",
                self.stack_output,
            )
            output_func = partial(  # type: ignore
                self._dm_dir_output, self.stack_output
            )

        report = DependencyMonkeyReport()
        for count, product in enumerate(
            self.asa.anneal_products(with_devel=with_devel)
        ):
            count += 1
            _LOGGER.info(
                "Submitting stack %d with score %g and justification:\n%s",
                count,
                product.score,
                json.dumps(product.justification),
            )

            try:
                response: Optional[str] = output_func(count, product.project)
            except Exception as exc:
                _LOGGER.exception("Failed to submit produced project: %s", str(exc))
                report.inc_skipped()
                continue

            if response is not None:
                _LOGGER.debug("Submitted results to %r", response)
                report.add_response(response)

        report.set_temperature_history(self.asa.get_temperature_history())
        return report

    @staticmethod
    def _dm_amun_output(
        output: str, context: Dict[Any, Any], count: int, generated_project: Project
    ) -> str:
        """A wrapper around Amun inspection call."""
        context = dict(context)
        context["python"] = generated_project.to_dict()
        response = amun_inspect(output, **context)
        _LOGGER.info(
            "Submitted Amun inspection #%d: %r", count, response["inspection_id"]
        )
        _LOGGER.debug("Full Amun response: %s", response)
        inspection_id: str = response["inspection_id"]
        return inspection_id

    @staticmethod
    def _dm_dir_output(output: str, count: int, generated_project: Project) -> str:
        """A wrapper for placing generated software stacks onto filesystem."""
        _LOGGER.debug("Writing stack %d", count)

        path = os.path.join(output, f"{count:d}")
        os.makedirs(path, exist_ok=True)

        _LOGGER.info("Writing project into output directory %r", path)
        generated_project.to_files(
            os.path.join(path, "Pipfile"), os.path.join(path, "Pipfile.lock")
        )

        return path

    @staticmethod
    def _dm_stdout_output(count: int, generated_project: Project) -> None:
        """A function called if the project should be printed to stdout as a dict."""
        _LOGGER.debug("Printing stack %d", count)
        json.dump(generated_project.to_dict(), fp=sys.stdout, sort_keys=True, indent=2)
        return None
