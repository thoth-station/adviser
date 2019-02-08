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

"""User configuration for adviser - supplied on any request."""

import os
import logging

import attr
import click
import yaml

from .entry import ConfigEntry

from ..enums import RecommendationType
from ..enums import PythonRecommendationOutput
from ..exceptions import UserConfigError

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class UserConfig:
    """User configuration options for advises."""

    _DEFAULT_RECOMMENDATION_TYPE = RecommendationType.STABLE
    _DEFAULT_REQUIREMENTS_FORMAT = PythonRecommendationOutput.PIPENV

    recommendation_type = attr.ib(type=RecommendationType, default=_DEFAULT_RECOMMENDATION_TYPE)
    requirements_format = attr.ib(type=PythonRecommendationOutput, default=_DEFAULT_REQUIREMENTS_FORMAT)
    configurations = attr.ib(type=list, default=attr.Factory(list))

    @classmethod
    def load(cls, string: str = None):
        """Transparently load the user configuration entry.

        Detect if the config is supplied as a string or as a path to configuration file.
        """
        if string is None:
            # Create one default configuration if no configurations were provided.
            _LOGGER.warning("No user configuration provided, using generic default values")
            return cls.from_dict({"configurations": [{}]})

        if os.path.isfile(string):
            return cls.from_file(string)
        else:
            return cls.from_string(string)

    @classmethod
    def from_string(cls, string: str):
        """Parse user configuration from string representation - serialized YAML or JSON is supported."""
        try:
            content = yaml.load(string)
        except Exception as exc:
            raise UserConfigError("Unable to parse configuration file - not a valid YAML/JSON") from exc

        return cls.from_dict(content)

    @classmethod
    def from_file(cls, file_path: str):
        """Parse user configuration from a file supplied."""
        try:
            with open(file_path, "r") as config_file:
                content = config_file.read()
        except Exception as exc:
            raise UserConfigError("Failed to read user configuration file from file %r: %s", file_path, str(exc))

        return cls.from_string(content)

    @classmethod
    def from_dict(cls, dict_: dict):
        """Parse the configuration file from a dictionary."""
        dict_ = dict(dict_)

        configurations = []
        for configuration_entry in dict_.pop("configurations", []):
            configurations.append(ConfigEntry.from_dict(configuration_entry))

        # Is instance checks are for compatibility for to_dict() and from_dict().
        recommendation_type = dict_.pop("recommendation_type", cls._DEFAULT_RECOMMENDATION_TYPE.name)
        if isinstance(recommendation_type, str):
            recommendation_type = RecommendationType.by_name(recommendation_type)

        requirements_format = dict_.pop("requirements_format", cls._DEFAULT_REQUIREMENTS_FORMAT.name)
        if isinstance(requirements_format, str):
            requirements_format = PythonRecommendationOutput.by_name(requirements_format)

        for key, value in dict_.items():
            if key == "managers":
                # Skip managers configuration option.
                continue

            _LOGGER.warning("Unknown configuration entry %r with value: %r", key, value)

        instance = cls(
            recommendation_type=recommendation_type,
            requirements_format=requirements_format,
            configurations=configurations,
        )
        return instance

    def to_dict(self):
        """Return the representation as a dict."""
        return attr.asdict(self)

    def report_core_options(self) -> None:
        """Report core configuration options."""
        click.echo("== Recommendation type: %s" % self.recommendation_type.name)
        click.echo("== Requirements format: %s" % self.requirements_format.name)

    def report(self) -> None:
        """Report all the configuration options."""
        self.report_core_options()
        for configuration_option in self.configurations:
            click.echo("== Configuration:\t")
            configuration_option.report()
