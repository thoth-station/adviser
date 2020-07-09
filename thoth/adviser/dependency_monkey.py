#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2018, 2019, 2020 Fridolin Pokorny
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
from functools import partial

import attr
import amun
from thoth.python import Project

from .beam import Beam
from .dm_report import DependencyMonkeyReport
from .predictor import Predictor
from .resolver import Resolver
from .enums import DecisionType


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class DependencyMonkey:
    """Dependency monkey creates stacks based on the configuration using ASA."""

    resolver = attr.ib(type=Resolver, kw_only=True)
    stack_output = attr.ib(type=str, kw_only=True, default="-")
    context = attr.ib(type=Optional[Dict[Any, Any]], default=attr.Factory(dict), kw_only=True)
    dry_run = attr.ib(type=bool, default=False, kw_only=True)
    decision_type = attr.ib(type=DecisionType, default=DecisionType.ALL, kw_only=True)

    @property
    def predictor(self) -> Predictor:
        """Get predictor for the current dependency monkey configuration."""
        return self.resolver.predictor

    @property
    def beam(self) -> Beam:
        """Get beam instance used in the resolver."""
        return self.resolver.beam

    def resolve(self, *, with_devel: bool = True, user_stack_scoring: bool = False) -> DependencyMonkeyReport:
        """Perform simulated annealing and run dependency monkey on products."""
        if user_stack_scoring:
            _LOGGER.warning("Ignoring user_stack_scoring flag in dependency monkey runs")
        if self.dry_run:
            _LOGGER.warning("Dry run of Dependency Monkey is set, stacks will be just computed")
            output_func = partial(self._dm_dry_run, self.stack_output)
        elif self.stack_output == "-":
            _LOGGER.debug("Results of Dependency Monkey run will be printed to standard output")
            output_func = self._dm_stdout_output  # type: ignore
        elif self.stack_output.startswith(("https://", "http://")):
            _LOGGER.debug(
                "Results of Dependency Monkey run will be submitted to API endpoint %r", self.stack_output,
            )
            output_func = partial(self._dm_amun_output, self.stack_output, self.context or {})  # type: ignore
        else:
            _LOGGER.debug(
                "Results of Dependency Monkey run will be stored in directory %r", self.stack_output,
            )
            output_func = partial(self._dm_dir_output, self.stack_output)  # type: ignore

        report = DependencyMonkeyReport()
        for count, product in enumerate(self.resolver.resolve_products(with_devel=with_devel)):
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
                report.skipped += 1
                continue

            if response is not None:
                _LOGGER.debug("Submitted results to %r", response)
                report.add_response(response, product)

        # Call post-run report function with the report once all is done as we used lower
        # level resolver method `resolve_products' and this object maintains report.
        self.resolver.pipeline.call_post_run_report(report)
        return report

    @staticmethod
    def _dm_dry_run(output: str, count: int, _: Project) -> None:  # noqa: D401
        """A wrapper around dry-run flag."""
        _LOGGER.info("Stack %d would be outputted to %r, but dry run flag was set, skipping...", count, output)
        return None

    @staticmethod
    def _dm_amun_output(
        output: str, context: Dict[Any, Any], count: int, generated_project: Project
    ) -> str:  # noqa: D401
        """A wrapper around Amun inspection call."""
        context = dict(context)
        context["python"] = generated_project.to_dict()
        # No need to supply runtime environment information.
        context["python"].pop("runtime_environment", None)
        response = amun.inspect(output, **context)
        _LOGGER.info("Submitted Amun inspection #%d: %r", count, response["inspection_id"])
        _LOGGER.debug("Full Amun response: %s", response)
        inspection_id: str = response["inspection_id"]
        return inspection_id

    @staticmethod
    def _dm_dir_output(output: str, count: int, generated_project: Project) -> str:  # noqa: D401
        """A wrapper for placing generated software stacks onto filesystem."""
        _LOGGER.debug("Writing stack %d", count)

        path = os.path.join(output, f"{count:d}")
        os.makedirs(path, exist_ok=True)

        _LOGGER.info("Writing project into output directory %r", path)
        generated_project.to_files(os.path.join(path, "Pipfile"), os.path.join(path, "Pipfile.lock"))

        return path

    @staticmethod
    def _dm_stdout_output(count: int, generated_project: Project) -> None:  # noqa: D401
        """A function called if the project should be printed to stdout as a dict."""
        _LOGGER.debug("Printing stack %d", count)
        json.dump(generated_project.to_dict(), fp=sys.stdout, sort_keys=True, indent=2)
        return None
