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

"""Test manipulation with a pipeline product."""

from collections import OrderedDict

import flexmock

from thoth.adviser.product import Product
from thoth.adviser.state import State
from thoth.common import RuntimeEnvironment
from thoth.python import PackageVersion
from thoth.python import Source

from .base import AdviserTestCase


class TestProduct(AdviserTestCase):
    """Test manipulation with product."""

    def test_from_final_state(self) -> None:
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
            advised_runtime_environment=RuntimeEnvironment.from_dict(
                {"python_version": "3.6"}
            ),
        )
        state.add_justification([{"foo": "bar"}])

        pypi = Source("https://pypi.org/simple")

        pv_daiquiri_locked = PackageVersion(
            name="daiquiri", version="==1.6.0", index=pypi, develop=False
        )
        pv_numpy_locked = PackageVersion(
            name="numpy", version="==1.17.4", index=pypi, develop=False
        )
        pv_tensorflow_locked = PackageVersion(
            name="tensorflow", version="==2.0.0", index=pypi, develop=False
        )

        context = flexmock()
        graph = flexmock()

        context.should_receive("get_package_version").with_args(
            ("daiquiri", "1.6.0", "https://pypi.org/simple")
        ).and_return(pv_daiquiri_locked).ordered()
        graph.should_receive("get_python_package_hashes_sha256").with_args(
            "daiquiri", "1.6.0", "https://pypi.org/simple"
        ).and_return(["000"]).ordered()

        context.should_receive("get_package_version").with_args(
            ("numpy", "1.17.4", "https://pypi.org/simple")
        ).and_return(pv_numpy_locked).ordered()
        graph.should_receive("get_python_package_hashes_sha256").with_args(
            "numpy", "1.17.4", "https://pypi.org/simple"
        ).and_return(["111"]).ordered()

        context.should_receive("get_package_version").with_args(
            ("tensorflow", "2.0.0", "https://pypi.org/simple")
        ).and_return(pv_tensorflow_locked).ordered()
        graph.should_receive("get_python_package_hashes_sha256").with_args(
            "tensorflow", "2.0.0", "https://pypi.org/simple"
        ).and_return(["222"]).ordered()

        pv_daiquiri = PackageVersion(
            name="daiquiri", version="*", index=pypi, develop=False
        )
        pv_tensorflow = PackageVersion(
            name="tensorflow", version=">=2.0.0", index=pypi, develop=False
        )

        project = flexmock()
        project.should_receive("iter_dependencies").with_args(
            with_devel=True
        ).and_return([pv_daiquiri, pv_tensorflow]).once()

        product = Product.from_final_state(
            state=state, graph=graph, project=project, context=context
        )

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
                "source": [
                    {
                        "url": "https://pypi.org/simple",
                        "verify_ssl": True,
                        "name": "pypi-org",
                    }
                ],
            },
            "requirements_locked": {
                "_meta": {
                    "sources": [
                        {
                            "url": "https://pypi.org/simple",
                            "verify_ssl": True,
                            "name": "pypi-org",
                        }
                    ],
                    "requires": {},
                    "hash": {
                        "sha256": "c3a2f42932b6e5cd30f5664b11eda605f5fbd672f1b88729561d0d3edd10b5d9"
                    },
                    "pipfile-spec": 6,
                },
                "default": {
                    "daiquiri": {
                        "version": "==1.6.0",
                        "hashes": ["000"],
                        "index": "pypi-org",
                    },
                    "numpy": {
                        "version": "==1.17.4",
                        "hashes": ["111"],
                        "index": "pypi-org",
                    },
                    "tensorflow": {
                        "version": "==2.0.0",
                        "hashes": ["222"],
                        "index": "pypi-org",
                    },
                },
                "develop": {},
            },
            "runtime_environment": {
                "hardware": {"cpu_family": None, "cpu_model": None},
                "operating_system": {"name": None, "version": None},
                "python_version": None,
                "cuda_version": None,
                "name": None,
            },
        }

    def test_to_dict(self) -> None:
        """Test conversion of this product into a dictionary representation."""
        project = flexmock()
        project.should_receive("to_dict").with_args().and_return({"baz": "bar"}).once()

        advised_runtime_environment = flexmock()
        advised_runtime_environment.should_receive("to_dict").with_args().and_return(
            {"hello": "thoth"}
        ).once()

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
