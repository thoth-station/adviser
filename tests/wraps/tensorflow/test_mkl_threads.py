#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020 Fridolin Pokorny
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

"""Test wrap adding information about Intel's MKL env variable configuration."""

import jsonpatch
import yaml

from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.state import State
from thoth.adviser.wraps import MKLThreadsWrap

from ...base import AdviserUnitTestCase


class TestMKLThreadsWrap(AdviserUnitTestCase):
    """Test Intel's MKL thread env info wrap."""

    _DEPLOYMENT_CONFIG = """\
apiVersion: apps.openshift.io/v1
kind: DeploymentConfig
metadata:
  name: foo
  namespace: some-namespace
spec:
  replicas: 1
  selector:
    service: foo
  template:
    spec:
      containers:
      - image: "foo:latest"
        env:
        - name: APP_MODULE
          value: "foo"
"""

    UNIT_TESTED = MKLThreadsWrap

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.recommendation_type = RecommendationType.LATEST

        for package_name in ("torch", "pytorch", "intel-tensorflow"):
            pipeline_config = self.UNIT_TESTED.should_include(builder_context)
            assert pipeline_config is not None
            assert pipeline_config == {"package_name": package_name}

            unit = self.UNIT_TESTED()
            unit.update_configuration(pipeline_config)

            builder_context.add_unit(unit)

        assert self.UNIT_TESTED.should_include(builder_context) is None, "The unit must not be included"

    def test_run_justification_noop(self) -> None:
        """Test no operation when PyTorch is not present."""
        state = State()
        state.add_resolved_dependency(("micropipenv", "0.1.4", "https://pypi.org/simple"))
        assert not state.justification

        unit = MKLThreadsWrap()
        unit.run(state)

        assert len(state.justification) == 0

    def test_run_add_justification(self) -> None:
        """Test adding information Intel's MKL environment variable."""
        state = State()
        state.add_resolved_dependency(("pytorch", "1.4.0", "https://pypi.org/simple"))
        assert len(state.advised_manifest_changes) == 0
        assert not state.justification

        unit = MKLThreadsWrap()
        unit.run(state)

        assert len(state.justification) == 1
        assert set(state.justification[0].keys()) == {"type", "message", "link"}
        assert state.justification[0]["type"] == "WARNING"
        assert state.justification[0]["link"], "Empty link to justification document provided"
        assert len(state.advised_manifest_changes) == 1
        assert state.advised_manifest_changes[0] == [
            {
                "apiVersion:": "apps.openshift.io/v1",
                "kind": "DeploymentConfig",
                "patch": {
                    "op": "add",
                    "path": "/spec/template/spec/containers/0/env/0",
                    "value": {"name": "OMP_NUM_THREADS", "value": "1"},
                },
            }
        ]
        patch = jsonpatch.JsonPatch(obj["patch"] for obj in state.advised_manifest_changes[0])
        deployment_config = yaml.safe_load(self._DEPLOYMENT_CONFIG)
        assert jsonpatch.apply_patch(deployment_config, patch) == {
            "apiVersion": "apps.openshift.io/v1",
            "kind": "DeploymentConfig",
            "metadata": {"name": "foo", "namespace": "some-namespace"},
            "spec": {
                "replicas": 1,
                "selector": {"service": "foo"},
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "env": [
                                    {"name": "OMP_NUM_THREADS", "value": "1"},
                                    {"name": "APP_MODULE", "value": "foo"},
                                ],
                                "image": "foo:latest",
                            }
                        ]
                    }
                },
            },
        }
