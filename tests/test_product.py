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

"""Test manipulation with a pipeline product."""

from collections import OrderedDict

import flexmock

from thoth.adviser.product import Product
from thoth.adviser.state import State
from thoth.adviser.context import Context
from thoth.common import RuntimeEnvironment
from thoth.python import PackageVersion
from thoth.python import Pipfile
from thoth.python import Source

from .base import AdviserTestCase


class TestProduct(AdviserTestCase):
    """Test manipulation with product."""

    _PIPFILE = """
[[source]]
name = "pypi-org"
url = "https://pypi.org/simple"
verify_ssl = true

[dev-packages]

[packages]
tensorflow = "*"

[requires]
python_version = "3.7"
"""

    def test_from_final_state(self, context: Context) -> None:
        """Test instantiating product from a final state."""
        state = State(
            score=0.5,
            resolved_dependencies=OrderedDict(
                {
                    "daiquiri": ("daiquiri", "1.6.0", "https://pypi.org/simple"),
                    "numpy": ("numpy", "1.17.4", "https://pypi.org/simple"),
                    "tensorflow": ("tensorflow", "2.0.0", "https://pypi.org/simple"),
                }
            ),
            unresolved_dependencies=OrderedDict(),
            advised_runtime_environment=RuntimeEnvironment.from_dict({"python_version": "3.6"}),
        )
        state.add_justification([{"foo": "bar"}])

        pypi = Source("https://pypi.org/simple")

        pv_daiquiri_locked = PackageVersion(name="daiquiri", version="==1.6.0", index=pypi, develop=False)
        pv_numpy_locked = PackageVersion(name="numpy", version="==1.17.4", index=pypi, develop=False)
        pv_tensorflow_locked = PackageVersion(name="tensorflow", version="==2.0.0", index=pypi, develop=False)

        context.should_receive("get_package_version").with_args(
            ("daiquiri", "1.6.0", "https://pypi.org/simple"), graceful=False
        ).and_return(pv_daiquiri_locked).ordered()
        context.graph.should_receive("get_python_package_hashes_sha256").with_args(
            "daiquiri", "1.6.0", "https://pypi.org/simple"
        ).and_return(["000"]).ordered()

        context.should_receive("get_package_version").with_args(
            ("numpy", "1.17.4", "https://pypi.org/simple"), graceful=False
        ).and_return(pv_numpy_locked).ordered()
        context.graph.should_receive("get_python_package_hashes_sha256").with_args(
            "numpy", "1.17.4", "https://pypi.org/simple"
        ).and_return(["111"]).ordered()

        context.should_receive("get_package_version").with_args(
            ("tensorflow", "2.0.0", "https://pypi.org/simple"), graceful=False
        ).and_return(pv_tensorflow_locked).ordered()
        context.graph.should_receive("get_python_package_hashes_sha256").with_args(
            "tensorflow", "2.0.0", "https://pypi.org/simple"
        ).and_return(["222"]).ordered()

        pv_daiquiri = PackageVersion(name="daiquiri", version="*", index=pypi, develop=False)
        pv_tensorflow = PackageVersion(name="tensorflow", version=">=2.0.0", index=pypi, develop=False)

        project = flexmock(
            pipfile=Pipfile.from_string(self._PIPFILE),
            runtime_environment=RuntimeEnvironment.from_dict({"operating_system": {"name": "rhel"}}),
        )
        project.should_receive("iter_dependencies").with_args(with_devel=True).and_return(
            [pv_daiquiri, pv_tensorflow]
        ).once()

        context.project = project
        context.dependencies = {
            "daiquiri": {("daiquiri", "1.6.0", "https://pypi.org/simple"): set(),},
            "numpy": {("numpy", "1.17.4", "https://pypi.org/simple"): set()},
            "tensorflow": {
                ("tensorflow", "2.0.0", "https://pypi.org/simple"): {("numpy", "1.17.4", "https://pypi.org/simple")}
            },
        }
        context.dependents = {
            "daiquiri": {("daiquiri", "1.6.0", "https://pypi.org/simple"): set(),},
            "numpy": {
                ("numpy", "1.17.4", "https://pypi.org/simple"): {
                    (("tensorflow", "2.0.0", "https://pypi.org/simple"), "fedora", "31", "3.7",)
                }
            },
            "tensorflow": {("tensorflow", "2.0.0", "https://pypi.org/simple"): set()},
        }
        context.graph.should_receive("get_python_environment_marker").with_args(
            "tensorflow",
            "2.0.0",
            "https://pypi.org/simple",
            dependency_name="numpy",
            dependency_version="1.17.4",
            os_name="fedora",
            os_version="31",
            python_version="3.7",
        ).and_return("python_version >= '3.7'").once()
        product = Product.from_final_state(state=state, context=context)

        assert product.score == state.score
        assert product.justification == state.justification
        assert product.advised_runtime_environment == state.advised_runtime_environment
        assert product.project.to_dict() == {
            "requirements": {
                "packages": {
                    "daiquiri": {"index": "pypi-org", "version": "*"},
                    "tensorflow": {"index": "pypi-org", "version": ">=2.0.0"},
                },
                "dev-packages": {},
                "requires": {"python_version": "3.7"},
                "source": [{"url": "https://pypi.org/simple", "verify_ssl": True, "name": "pypi-org",}],
            },
            "requirements_locked": {
                "_meta": {
                    "sources": [{"url": "https://pypi.org/simple", "verify_ssl": True, "name": "pypi-org",}],
                    "requires": {"python_version": "3.7"},
                    "hash": {"sha256": "f08689732b596fd705a45bbf9ec44c3995b17a1aa6392c46500aeb736c4d4e88"},
                    "pipfile-spec": 6,
                },
                "default": {
                    "daiquiri": {"version": "==1.6.0", "hashes": ["sha256:000"], "index": "pypi-org",},
                    "numpy": {
                        "version": "==1.17.4",
                        "hashes": ["sha256:111"],
                        "index": "pypi-org",
                        "markers": "python_version >= '3.7'",
                    },
                    "tensorflow": {"version": "==2.0.0", "hashes": ["sha256:222"], "index": "pypi-org",},
                },
                "develop": {},
            },
            "runtime_environment": {
                "hardware": {"cpu_family": None, "cpu_model": None},
                "operating_system": {"name": "rhel", "version": None},
                "python_version": None,
                "cuda_version": None,
                "name": None,
                "platform": None,
            },
        }

    def test_to_dict(self) -> None:
        """Test conversion of this product into a dictionary representation."""
        project = flexmock()
        project.should_receive("to_dict").with_args().and_return({"baz": "bar"}).once()

        advised_runtime_environment = flexmock()
        advised_runtime_environment.should_receive("to_dict").with_args().and_return({"hello": "thoth"}).once()

        product = Product(
            score=0.999,
            project=project,
            justification=[{"foo": "bar"}],
            advised_runtime_environment=advised_runtime_environment,
        )

        assert product.to_dict() == {
            "score": 0.999,
            "project": {"baz": "bar"},
            "justification": [{"foo": "bar"}],
            "advised_runtime_environment": {"hello": "thoth"},
        }

    def test_environment_markers(self, context: Context) -> None:
        """Test handling of environment markers across multiple runs."""
        state = State(
            score=0.0,
            resolved_dependencies=OrderedDict(
                {
                    "numpy": ("numpy", "1.0.0", "https://pypi.org/simple"),
                    "tensorflow": ("tensorflow", "2.0.0", "https://pypi.org/simple"),
                }
            ),
            unresolved_dependencies=OrderedDict(),
        )

        context.graph.should_receive("get_python_package_hashes_sha256").with_args(
            "numpy", "1.0.0", "https://pypi.org/simple"
        ).and_return(["000"]).once()

        context.graph.should_receive("get_python_package_hashes_sha256").with_args(
            "tensorflow", "2.0.0", "https://pypi.org/simple"
        ).and_return(["111"]).once()

        pypi = Source("https://pypi.org/simple")
        pv_numpy_locked = PackageVersion(name="numpy", version="==1.0.0", index=pypi, develop=False)
        pv_tensorflow_locked = PackageVersion(name="tensorflow", version="==2.0.0", index=pypi, develop=False)

        context.should_receive("get_package_version").with_args(
            ("numpy", "1.0.0", "https://pypi.org/simple"), graceful=False
        ).and_return(pv_numpy_locked).twice()

        context.should_receive("get_package_version").with_args(
            ("tensorflow", "2.0.0", "https://pypi.org/simple"), graceful=False
        ).and_return(pv_tensorflow_locked).twice()

        context.dependents = {
            "numpy": {
                ("numpy", "1.0.0", "https://pypi.org/simple"): {
                    (("tensorflow", "2.0.0", "https://pypi.org/simple"), "fedora", "31", "3.7",)
                }
            },
            "tensorflow": {("tensorflow", "2.0.0", "https://pypi.org/simple"): set()},
        }

        context.graph.should_receive("get_python_environment_marker").with_args(
            "tensorflow",
            "2.0.0",
            "https://pypi.org/simple",
            dependency_name="numpy",
            dependency_version="1.0.0",
            os_name="fedora",
            os_version="31",
            python_version="3.7",
        ).and_return("python_version >= '3.7'").and_return("python_version >= '3' or 1").twice()

        product = Product.from_final_state(context=context, state=state)
        expected = {
            "advised_runtime_environment": None,
            "justification": [],
            "project": {
                "requirements": {
                    "dev-packages": {},
                    "packages": {"flask": "*", "tensorflow": "==1.9.0"},
                    "requires": {"python_version": "3.6"},
                    "source": [
                        {"name": "pypi", "url": "https://pypi.org/simple", "verify_ssl": True,},
                        {"name": "pypi-org", "url": "https://pypi.org/simple", "verify_ssl": True,},
                    ],
                },
                "requirements_locked": {
                    "_meta": {
                        "hash": {"sha256": "e55b6bbaba9467f1629c34e7a4180a6a2d82df37e02e762866e7aac27ced0f99"},
                        "pipfile-spec": 6,
                        "requires": {"python_version": "3.6"},
                        "sources": [
                            {"name": "pypi", "url": "https://pypi.org/simple", "verify_ssl": True,},
                            {"name": "pypi-org", "url": "https://pypi.org/simple", "verify_ssl": True,},
                        ],
                    },
                    "default": {
                        "numpy": {
                            "hashes": ["sha256:000"],
                            "index": "pypi-org",
                            "markers": "python_version >= '3.7'",
                            "version": "==1.0.0",
                        },
                        "tensorflow": {"hashes": ["sha256:111"], "index": "pypi-org", "version": "==2.0.0",},
                    },
                    "develop": {},
                },
                "runtime_environment": {
                    "cuda_version": None,
                    "hardware": {"cpu_family": None, "cpu_model": None},
                    "name": None,
                    "operating_system": {"name": None, "version": None},
                    "python_version": None,
                    "platform": None,
                },
            },
            "score": 0.0,
        }

        assert product.to_dict() == expected

        # Markers should not intersect.
        product = Product.from_final_state(context=context, state=state)
        expected["project"]["requirements_locked"]["default"]["numpy"]["markers"] = "python_version >= '3' or 1"
        assert product.to_dict() == expected
