#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019 - 2021 Fridolin Pokorny
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


import os
import json
import flexmock
from itertools import chain

from thoth.adviser.product import Product
from thoth.adviser.state import State
from thoth.adviser.context import Context
from thoth.common import get_justification_link as jl
from thoth.common import RuntimeEnvironment
from thoth.python import PackageVersion
from thoth.python import Pipfile
from thoth.python import PipfileLock
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

[thoth.allow_prereleases]
black = true
"""

    _DEPENDENCIES_NO_CYCLE = {
        "absl-py": {
            ("absl-py", "0.8.1", "https://pypi.org/simple"): {
                ("six", "1.13.0", "https://pypi.org/simple"),
                ("six", "1.9.0", "https://pypi.org/simple"),
            }
        },
        "astor": {
            ("astor", "0.8.0", "https://pypi.org/simple"): {
                ("six", "1.13.0", "https://pypi.org/simple"),
            }
        },
        "tensorflow": {
            ("tensorflow", "1.9.0", "https://pypi.org/simple"): {
                ("astor", "0.8.0", "https://pypi.org/simple"),
                ("absl-py", "0.8.1", "https://pypi.org/simple"),
            }
        },
    }

    _DEPENDENCIES_CYCLE = {
        "a": {
            ("a", "1.0.0", "https://pypi.org/simple"): {
                ("b", "1.0.0", "https://pypi.org/simple"),
            }
        },
        "b": {
            ("b", "1.0.0", "https://pypi.org/simple"): {
                ("c", "1.1.0", "https://pypi.org/simple"),
            }
        },
        "c": {
            ("c", "1.0.0", "https://pypi.org/simple"): {
                ("a", "1.0.0", "https://pypi.org/simple"),
                ("b", "1.0.0", "https://pypi.org/simple"),
            }
        },
    }

    _DEPENDENCIES_NO_CYCLE_PIPFILE_LOCK = PipfileLock.from_dict(
        {
            "_meta": {
                "hash": {"sha256": "001e85311f65a97fe23d21061c0b68139015dfea5b4bfb8b91551ede367fe1d1"},
                "pipfile-spec": 6,
                "requires": {"python_version": "3.6"},
                "sources": [{"name": "pypi", "url": "https://pypi.org/simple", "verify_ssl": True}],
            },
            "default": {
                "absl-py": {
                    "hashes": ["sha256:d9129186431e150d7fe455f1cb1ecbb92bb5dba9da9bc3ef7b012d98c4db2526"],
                    "index": "pypi",
                    "version": "==0.8.1",
                },
                "astor": {
                    "hashes": [
                        "sha256:37a6eed8b371f1228db08234ed7f6cfdc7817a3ed3824797e20cbb11dc2a7862",
                    ],
                    "index": "pypi",
                    "version": "==0.8.0",
                },
                "six": {
                    "hashes": [
                        "sha256:13f9f196f330c7c2c5d7a5cf91af894110ca0215ac051b5844701f2bfd934d52",
                    ],
                    "index": "pypi",
                    "version": "==1.13.0",
                },
                "tensorflow": {
                    "hashes": [
                        "sha256:d351f7db08b8de322536c5886fada3e37feae809bfd37368050f9eeea544b87e",
                    ],
                    "index": "pypi",
                    "version": "==1.9.0",
                },
            },
            "develop": {},
        },
        pipfile=None,
    )

    _DEPENDENCIES_CYCLE_PIPFILE_LOCK = PipfileLock.from_dict(
        {
            "_meta": {
                "hash": {"sha256": "FOO"},
                "pipfile-spec": 6,
                "requires": {"python_version": "3.8"},
                "sources": [{"name": "pypi", "url": "https://pypi.org/simple", "verify_ssl": True}],
            },
            "default": {
                "a": {
                    "hashes": ["sha256:foo"],
                    "index": "pypi",
                    "version": "==1.0.0",
                },
                "b": {
                    "hashes": ["sha256:foo"],
                    "index": "pypi",
                    "version": "==1.0.0",
                },
                "c": {
                    "hashes": ["sha256:foo"],
                    "index": "pypi",
                    "version": "==1.0.0",
                },
            },
            "develop": {},
        },
        pipfile=None,
    )

    def test_from_final_state(self, context: Context) -> None:
        """Test instantiating product from a final state."""
        state = State(
            score=0.5,
            resolved_dependencies={
                "daiquiri": ("daiquiri", "1.6.0", "https://pypi.org/simple"),
                "numpy": ("numpy", "1.17.4", "https://pypi.org/simple"),
                "tensorflow": ("tensorflow", "2.0.0", "https://pypi.org/simple"),
            },
            unresolved_dependencies={},
            advised_runtime_environment=RuntimeEnvironment.from_dict({"python_version": "3.6"}),
        )
        state.add_justification(self.JUSTIFICATION_SAMPLE_1)

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
            "daiquiri": {
                ("daiquiri", "1.6.0", "https://pypi.org/simple"): set(),
            },
            "numpy": {("numpy", "1.17.4", "https://pypi.org/simple"): set()},
            "tensorflow": {
                ("tensorflow", "2.0.0", "https://pypi.org/simple"): {("numpy", "1.17.4", "https://pypi.org/simple")}
            },
        }
        context.dependents = {
            "daiquiri": {
                ("daiquiri", "1.6.0", "https://pypi.org/simple"): set(),
            },
            "numpy": {
                ("numpy", "1.17.4", "https://pypi.org/simple"): {
                    (
                        ("tensorflow", "2.0.0", "https://pypi.org/simple"),
                        "fedora",
                        "31",
                        "3.7",
                    )
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

        assert "THOTH_ADVISER_METADATA" not in os.environ
        metadata_justification = {"thoth.adviser": {"justification": [{"bar": "baz"}]}}
        os.environ["THOTH_ADVISER_METADATA"] = json.dumps(metadata_justification)
        try:
            product = Product.from_final_state(state=state, context=context)
        finally:
            os.environ.pop("THOTH_ADVISER_METADATA")

        assert product.score == state.score
        assert product.justification == list(
            chain(metadata_justification["thoth.adviser"]["justification"], state.justification)
        )
        assert product.advised_runtime_environment == state.advised_runtime_environment
        assert product.project.to_dict() == {
            "constraints": [],
            "requirements": {
                "packages": {
                    "daiquiri": {"index": "pypi-org-simple", "version": "*"},
                    "tensorflow": {"index": "pypi-org-simple", "version": ">=2.0.0"},
                },
                "dev-packages": {},
                "requires": {"python_version": "3.7"},
                "source": [
                    {
                        "url": "https://pypi.org/simple",
                        "verify_ssl": True,
                        "name": "pypi-org",
                    },
                    {
                        "url": "https://pypi.org/simple",
                        "verify_ssl": True,
                        "name": "pypi-org-simple",
                    },
                ],
                "thoth": {
                    "allow_prereleases": {"black": True},
                },
            },
            "requirements_locked": {
                "_meta": {
                    "sources": [
                        {"name": "pypi-org", "url": "https://pypi.org/simple", "verify_ssl": True},
                        {
                            "url": "https://pypi.org/simple",
                            "verify_ssl": True,
                            "name": "pypi-org-simple",
                        },
                    ],
                    "requires": {"python_version": "3.7"},
                    "hash": {"sha256": "6cc8365e799b949fb6cc564cea2d8e0e8a782ab676a006e65abbe14621b93381"},
                    "pipfile-spec": 6,
                },
                "default": {
                    "daiquiri": {
                        "version": "==1.6.0",
                        "hashes": ["sha256:000"],
                        "index": "pypi-org-simple",
                    },
                    "numpy": {
                        "version": "==1.17.4",
                        "hashes": ["sha256:111"],
                        "index": "pypi-org-simple",
                        "markers": "python_version >= '3.7'",
                    },
                    "tensorflow": {
                        "version": "==2.0.0",
                        "hashes": ["sha256:222"],
                        "index": "pypi-org-simple",
                    },
                },
                "develop": {},
            },
            "runtime_environment": {
                "hardware": {"cpu_family": None, "cpu_model": None, "gpu_model": None},
                "operating_system": {"name": "rhel", "version": None},
                "python_version": None,
                "cuda_version": None,
                "cudnn_version": None,
                "name": None,
                "platform": None,
                "base_image": None,
                "mkl_version": None,
                "openblas_version": None,
                "openmpi_version": None,
                "recommendation_type": None,
            },
        }

    def test_to_dict(self, context: Context) -> None:
        """Test conversion of this product into a dictionary representation."""
        project = context.project
        project.should_receive("to_dict").with_args(keep_thoth_section=True).and_return({"baz": "bar"}).once()

        advised_runtime_environment = flexmock()
        advised_runtime_environment.should_receive("to_dict").with_args().and_return({"hello": "thoth"}).once()

        advised_manifest_changes = [
            [
                {
                    "apiVersion": "apps.openshift.io/v1",
                    "kind": "DeploymentConfig",
                    "patch": {
                        "op": "add",
                        "path": "spec.template.spec.containers[0].env",
                        "value": {"name": "OMP_NUM_THREADS", "value": "1"},
                    },
                }
            ]
        ]

        product = Product(
            advised_manifest_changes=advised_manifest_changes,
            advised_runtime_environment=advised_runtime_environment,
            justification=[{"foo": "bar"}],
            project=project,
            score=0.999,
            context=context,
        )

        assert product.to_dict() == {
            "score": 0.999,
            "project": {"baz": "bar"},
            "justification": [{"foo": "bar"}],
            "advised_runtime_environment": {"hello": "thoth"},
            "advised_manifest_changes": advised_manifest_changes,
            "dependency_graph": {
                "edges": [],
                "nodes": [
                    "absl-py",
                    "astor",
                    "click",
                    "flask",
                    "gast",
                    "grpcio",
                    "itsdangerous",
                    "jinja2",
                    "markdown",
                    "markupsafe",
                    "numpy",
                    "protobuf",
                    "six",
                    "tensorboard",
                    "tensorflow",
                    "termcolor",
                    "werkzeug",
                    "wheel",
                ],
            },
        }

    def test_environment_markers(self, context: Context) -> None:
        """Test handling of environment markers across multiple runs."""
        state = State(
            score=0.0,
            resolved_dependencies={
                "numpy": ("numpy", "1.0.0", "https://pypi.org/simple"),
                "tensorflow": ("tensorflow", "2.0.0", "https://pypi.org/simple"),
            },
            unresolved_dependencies={},
            justification=[{"type": "INFO", "message": "Foo bar", "link": "https://thoth-station.ninja"}],
        )

        # Make sure tested packages are not direct dependencies. In such cases the behaviour is
        # different, see other tests.
        context.project.pipfile.packages.packages.pop("tensorflow", None)
        context.project.pipfile.packages.packages.pop("numpy", None)

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
                    (
                        ("tensorflow", "2.0.0", "https://pypi.org/simple"),
                        "fedora",
                        "31",
                        "3.7",
                    )
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
            "advised_manifest_changes": [],
            "advised_runtime_environment": None,
            "justification": [
                {
                    "link": "https://thoth-station.ninja",
                    "message": "Foo bar",
                    "type": "INFO",
                }
            ],
            "dependency_graph": {"edges": [], "nodes": ["numpy", "tensorflow"]},
            "project": {
                "constraints": [],
                "requirements": {
                    "dev-packages": {},
                    "packages": {"flask": "*"},
                    "requires": {"python_version": "3.6"},
                    "source": [
                        {
                            "name": "pypi",
                            "url": "https://pypi.org/simple",
                            "verify_ssl": True,
                        },
                        {
                            "name": "pypi-org-simple",
                            "url": "https://pypi.org/simple",
                            "verify_ssl": True,
                        },
                    ],
                    "thoth": {
                        "allow_prereleases": {},
                        "disable_index_adjustment": False,
                    },
                },
                "requirements_locked": {
                    "_meta": {
                        "hash": {"sha256": "2e49395dfa87159358e581bd22e656c27c0dab04894d1b137a14f85bb387ea51"},
                        "pipfile-spec": 6,
                        "requires": {"python_version": "3.6"},
                        "sources": [
                            {"name": "pypi", "url": "https://pypi.org/simple", "verify_ssl": True},
                            {
                                "name": "pypi-org-simple",
                                "url": "https://pypi.org/simple",
                                "verify_ssl": True,
                            },
                        ],
                    },
                    "default": {
                        "numpy": {
                            "hashes": ["sha256:000"],
                            "index": "pypi-org-simple",
                            "markers": "python_version >= '3.7'",
                            "version": "==1.0.0",
                        },
                        "tensorflow": {
                            "hashes": ["sha256:111"],
                            "index": "pypi-org-simple",
                            "version": "==2.0.0",
                        },
                    },
                    "develop": {},
                },
                "runtime_environment": {
                    "base_image": None,
                    "cuda_version": None,
                    "cudnn_version": None,
                    "hardware": {"cpu_family": None, "cpu_model": None, "gpu_model": None},
                    "name": None,
                    "operating_system": {"name": None, "version": None},
                    "openblas_version": None,
                    "openmpi_version": None,
                    "mkl_version": None,
                    "python_version": None,
                    "recommendation_type": None,
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

    def test_environment_markers_direct_dependency(self, context: Context) -> None:
        """Test handling environment markers for direct dependencies."""
        state = State(
            score=0.0,
            resolved_dependencies={
                "numpy": ("numpy", "1.0.0", "https://pypi.org/simple"),
                "tensorflow": ("tensorflow", "2.0.0", "https://pypi.org/simple"),
            },
            unresolved_dependencies={},
            justification=[{"type": "INFO", "message": "Foo bar", "link": "https://thoth-station.ninja"}],
        )

        pypi = Source("https://pypi.org/simple")

        # Let's assume tensorflow is our direct dependency with an environment marker set. It sets also an environment
        # marker for numpy.
        context.project.pipfile.packages.packages.pop("tensorflow", None)
        tf_package_version_direct = PackageVersion(
            name="tensorflow", version=">1.0.0", index=pypi, develop=False, markers="python_version >= '3.6'"
        )
        context.project.pipfile.add_package_version(tf_package_version_direct)
        # Just to make sure numpy is not in the direct dependency listing.
        context.project.pipfile.packages.packages.pop("numpy", None)

        pv_numpy_locked = PackageVersion(name="numpy", version="==1.0.0", index=pypi, develop=False)
        pv_tensorflow_locked = PackageVersion(name="tensorflow", version="==2.0.0", index=pypi, develop=False)

        context.graph.should_receive("get_python_package_hashes_sha256").with_args(
            *pv_numpy_locked.to_tuple()
        ).and_return(["000"]).once()

        context.graph.should_receive("get_python_package_hashes_sha256").with_args(
            *pv_tensorflow_locked.to_tuple()
        ).and_return(["111"]).once()

        context.should_receive("get_package_version").with_args(
            ("numpy", "1.0.0", "https://pypi.org/simple"), graceful=False
        ).and_return(pv_numpy_locked).once()

        context.should_receive("get_package_version").with_args(
            ("tensorflow", "2.0.0", "https://pypi.org/simple"), graceful=False
        ).and_return(pv_tensorflow_locked).once()

        context.dependents = {
            "numpy": {
                ("numpy", "1.0.0", "https://pypi.org/simple"): {
                    (
                        ("tensorflow", "2.0.0", "https://pypi.org/simple"),
                        "fedora",
                        "31",
                        "3.7",
                    )
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
        ).and_return("python_version >= '3.7'").once()

        product = Product.from_final_state(context=context, state=state)
        expected = {
            "advised_manifest_changes": [],
            "advised_runtime_environment": None,
            "justification": [
                {
                    "link": "https://thoth-station.ninja",
                    "message": "Foo bar",
                    "type": "INFO",
                }
            ],
            "dependency_graph": {"edges": [], "nodes": ["numpy", "tensorflow"]},
            "project": {
                "constraints": [],
                "requirements": {
                    "dev-packages": {},
                    "packages": {
                        "flask": "*",
                        "tensorflow": {
                            "index": "pypi-org-simple",
                            "markers": "python_version >= '3.6'",
                            "version": ">1.0.0",
                        },
                    },
                    "requires": {"python_version": "3.6"},
                    "source": [
                        {
                            "name": "pypi",
                            "url": "https://pypi.org/simple",
                            "verify_ssl": True,
                        },
                        {
                            "name": "pypi-org-simple",
                            "url": "https://pypi.org/simple",
                            "verify_ssl": True,
                        },
                    ],
                    "thoth": {
                        "allow_prereleases": {},
                        "disable_index_adjustment": False,
                    },
                },
                "requirements_locked": {
                    "_meta": {
                        "hash": {"sha256": "382cd84046246d08cf670a07c61628958dec76e05d2473bf936866fc54619f9a"},
                        "pipfile-spec": 6,
                        "requires": {"python_version": "3.6"},
                        "sources": [
                            {"name": "pypi", "url": "https://pypi.org/simple", "verify_ssl": True},
                            {
                                "name": "pypi-org-simple",
                                "url": "https://pypi.org/simple",
                                "verify_ssl": True,
                            },
                        ],
                    },
                    "default": {
                        "numpy": {
                            "hashes": ["sha256:000"],
                            "index": "pypi-org-simple",
                            "markers": "python_version >= '3.7'",
                            "version": "==1.0.0",
                        },
                        "tensorflow": {
                            "hashes": ["sha256:111"],
                            "index": "pypi-org-simple",
                            "markers": "python_version >= '3.6'",
                            "version": "==2.0.0",
                        },
                    },
                    "develop": {},
                },
                "runtime_environment": {
                    "base_image": None,
                    "cuda_version": None,
                    "cudnn_version": None,
                    "hardware": {"cpu_family": None, "cpu_model": None, "gpu_model": None},
                    "name": None,
                    "operating_system": {"name": None, "version": None},
                    "openblas_version": None,
                    "openmpi_version": None,
                    "mkl_version": None,
                    "python_version": None,
                    "recommendation_type": None,
                    "platform": None,
                },
            },
            "score": 0.0,
        }

        assert product.to_dict() == expected

    def test_environment_markers_shared(self, context: Context) -> None:
        """Test handling of environment markers when multiple dependencies share one."""
        state = State(
            score=0.0,
            resolved_dependencies={
                "pandas": ("pandas", "1.0.0", "https://pypi.org/simple"),
                "numpy": ("numpy", "1.0.0", "https://pypi.org/simple"),
                "tensorflow": ("tensorflow", "2.0.0", "https://pypi.org/simple"),
            },
            unresolved_dependencies={},
            justification=[{"type": "INFO", "message": "Foo bar", "link": "https://thoth-station.ninja"}],
        )

        # Make sure tested packages are not direct dependencies. In such cases the behaviour is
        # different, see other tests.
        context.project.pipfile.packages.packages.pop("pandas", None)
        context.project.pipfile.packages.packages.pop("numpy", None)
        context.project.pipfile.packages.packages.pop("tensorflow", None)

        context.graph.should_receive("get_python_package_hashes_sha256").with_args(
            "numpy", "1.0.0", "https://pypi.org/simple"
        ).and_return(["000"]).once()

        context.graph.should_receive("get_python_package_hashes_sha256").with_args(
            "tensorflow", "2.0.0", "https://pypi.org/simple"
        ).and_return(["111"]).once()

        context.graph.should_receive("get_python_package_hashes_sha256").with_args(
            "pandas", "1.0.0", "https://pypi.org/simple"
        ).and_return(["222"]).once()

        pypi = Source("https://pypi.org/simple")
        pv_numpy_locked = PackageVersion(name="numpy", version="==1.0.0", index=pypi, develop=False)
        pv_tensorflow_locked = PackageVersion(name="tensorflow", version="==2.0.0", index=pypi, develop=False)
        pv_pandas_locked = PackageVersion(name="pandas", version="==1.0.0", index=pypi, develop=False)

        context.should_receive("get_package_version").with_args(
            ("numpy", "1.0.0", "https://pypi.org/simple"), graceful=False
        ).and_return(pv_numpy_locked).once()

        context.should_receive("get_package_version").with_args(
            ("pandas", "1.0.0", "https://pypi.org/simple"), graceful=False
        ).and_return(pv_pandas_locked).once()

        context.should_receive("get_package_version").with_args(
            ("tensorflow", "2.0.0", "https://pypi.org/simple"), graceful=False
        ).and_return(pv_tensorflow_locked).once()

        context.dependents = {
            "numpy": {
                ("numpy", "1.0.0", "https://pypi.org/simple"): [  # set to list for reproducible runs.
                    (
                        ("tensorflow", "2.0.0", "https://pypi.org/simple"),
                        "fedora",
                        "31",
                        "3.7",
                    ),
                    (
                        ("pandas", "1.0.0", "https://pypi.org/simple"),
                        "fedora",
                        "31",
                        "3.7",
                    ),
                ]
            },
            "tensorflow": {("tensorflow", "2.0.0", "https://pypi.org/simple"): set()},
            "pandas": {("pandas", "1.0.0", "https://pypi.org/simple"): set()},
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
        ).and_return("python_version >= '3.8'").once()

        context.graph.should_receive("get_python_environment_marker").with_args(
            "pandas",
            "1.0.0",
            "https://pypi.org/simple",
            dependency_name="numpy",
            dependency_version="1.0.0",
            os_name="fedora",
            os_version="31",
            python_version="3.7",
        ).and_return(None).once()

        product = Product.from_final_state(context=context, state=state)
        expected = {
            "advised_manifest_changes": [],
            "advised_runtime_environment": None,
            "dependency_graph": {"edges": [], "nodes": ["pandas", "numpy", "tensorflow"]},
            "justification": [
                {
                    "link": "https://thoth-station.ninja",
                    "message": "Foo bar",
                    "type": "INFO",
                }
            ],
            "project": {
                "constraints": [],
                "requirements": {
                    "dev-packages": {},
                    "packages": {"flask": "*"},
                    "requires": {"python_version": "3.6"},
                    "source": [
                        {"name": "pypi", "url": "https://pypi.org/simple", "verify_ssl": True},
                        {"name": "pypi-org-simple", "url": "https://pypi.org/simple", "verify_ssl": True},
                    ],
                    "thoth": {
                        "allow_prereleases": {},
                        "disable_index_adjustment": False,
                    },
                },
                "requirements_locked": {
                    "_meta": {
                        "hash": {"sha256": "2e49395dfa87159358e581bd22e656c27c0dab04894d1b137a14f85bb387ea51"},
                        "pipfile-spec": 6,
                        "requires": {"python_version": "3.6"},
                        "sources": [
                            {"name": "pypi", "url": "https://pypi.org/simple", "verify_ssl": True},
                            {"name": "pypi-org-simple", "url": "https://pypi.org/simple", "verify_ssl": True},
                        ],
                    },
                    "default": {
                        "numpy": {"hashes": ["sha256:000"], "index": "pypi-org-simple", "version": "==1.0.0"},
                        "pandas": {"hashes": ["sha256:222"], "index": "pypi-org-simple", "version": "==1.0.0"},
                        "tensorflow": {"hashes": ["sha256:111"], "index": "pypi-org-simple", "version": "==2.0.0"},
                    },
                    "develop": {},
                },
                "runtime_environment": {
                    "base_image": None,
                    "cuda_version": None,
                    "cudnn_version": None,
                    "hardware": {"cpu_family": None, "cpu_model": None, "gpu_model": None},
                    "name": None,
                    "operating_system": {"name": None, "version": None},
                    "platform": None,
                    "mkl_version": None,
                    "openmpi_version": None,
                    "openblas_version": None,
                    "python_version": None,
                    "recommendation_type": None,
                },
            },
            "score": 0.0,
        }

        assert product.to_dict() == expected

    def test_no_observation(self, context: Context) -> None:
        """Test adding information about no justification added."""
        state = State(
            score=0.0,
            resolved_dependencies={
                "flask": ("flask", "0.12", "https://pypi.org/simple"),
            },
            unresolved_dependencies={},
        )

        context.project.pipfile.packages.packages.pop("tensorflow")

        context.graph.should_receive("get_python_package_hashes_sha256").with_args(
            "flask", "0.12", "https://pypi.org/simple"
        ).and_return(["222"]).once()

        pypi = Source("https://pypi.org/simple")
        pv_pandas_locked = PackageVersion(name="flask", version="==0.12", index=pypi, develop=False)

        context.should_receive("get_package_version").with_args(
            ("flask", "0.12", "https://pypi.org/simple"), graceful=False
        ).and_return(pv_pandas_locked).once()

        context.dependents = {
            "flask": {("flask", "0.12", "https://pypi.org/simple"): set()},
        }

        product = Product.from_final_state(context=context, state=state)
        expected = {
            "advised_manifest_changes": [],
            "advised_runtime_environment": None,
            "dependency_graph": {"edges": [], "nodes": ["flask"]},
            "justification": [
                {
                    "type": "INFO",
                    "message": "No issues spotted for this stack based on Thoth's database",
                    "link": jl("no_observations"),
                }
            ],
            "project": {
                "constraints": [],
                "requirements": {
                    "dev-packages": {},
                    "packages": {"flask": "*"},
                    "requires": {"python_version": "3.6"},
                    "source": [
                        {"name": "pypi", "url": "https://pypi.org/simple", "verify_ssl": True},
                        {"name": "pypi-org-simple", "url": "https://pypi.org/simple", "verify_ssl": True},
                    ],
                    "thoth": {
                        "allow_prereleases": {},
                        "disable_index_adjustment": False,
                    },
                },
                "requirements_locked": {
                    "_meta": {
                        "hash": {"sha256": "2e49395dfa87159358e581bd22e656c27c0dab04894d1b137a14f85bb387ea51"},
                        "pipfile-spec": 6,
                        "requires": {"python_version": "3.6"},
                        "sources": [
                            {"name": "pypi", "url": "https://pypi.org/simple", "verify_ssl": True},
                            {"name": "pypi-org-simple", "url": "https://pypi.org/simple", "verify_ssl": True},
                        ],
                    },
                    "default": {
                        "flask": {"hashes": ["sha256:222"], "index": "pypi-org-simple", "version": "==0.12"},
                    },
                    "develop": {},
                },
                "runtime_environment": {
                    "base_image": None,
                    "cuda_version": None,
                    "cudnn_version": None,
                    "hardware": {"cpu_family": None, "cpu_model": None, "gpu_model": None},
                    "name": None,
                    "operating_system": {"name": None, "version": None},
                    "platform": None,
                    "mkl_version": None,
                    "openmpi_version": None,
                    "openblas_version": None,
                    "python_version": None,
                    "recommendation_type": None,
                },
            },
            "score": 0.0,
        }

        assert product.to_dict() == expected

    def test_construct_dependency_graph_basic(self) -> None:
        """Test constructing dependency graph."""
        context = flexmock(dependencies=self._DEPENDENCIES_NO_CYCLE)
        dependency_graph = Product._construct_dependency_graph(context, self._DEPENDENCIES_NO_CYCLE_PIPFILE_LOCK)
        assert dependency_graph["nodes"] == ["absl-py", "astor", "six", "tensorflow"]
        assert set(tuple(i) for i in dependency_graph["edges"]) == {(0, 2), (1, 2), (3, 1), (3, 0)}

    def test_construct_dependency_graph_cycle(self, context: Context) -> None:
        """Test constructing dependency graph information with cycles."""
        context = flexmock(dependencies=self._DEPENDENCIES_CYCLE)
        dependency_graph = Product._construct_dependency_graph(context, self._DEPENDENCIES_CYCLE_PIPFILE_LOCK)
        assert dependency_graph["nodes"] == ["a", "b", "c"]
        assert set(tuple(i) for i in dependency_graph["edges"]) == {(0, 1), (2, 0), (2, 1)}
