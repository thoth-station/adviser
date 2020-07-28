"""Setup configuration for adviser module."""

import os
import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand  # noqa


def get_install_requires():
    """Get requirements for adviser module."""
    with open("requirements.txt", "r") as requirements_file:
        res = requirements_file.readlines()
        return [req.split(" ", maxsplit=1)[0] for req in res if req]


def get_version():
    """Get current version of adviser module."""
    with open(os.path.join("thoth", "adviser", "__init__.py")) as f:
        content = f.readlines()

    for line in content:
        if line.startswith("__version__ ="):
            # dirty, remove trailing and leading chars
            return line.split(" = ")[1][1:-2]
    raise ValueError("No version identifier found")


def read(fname):
    """Read."""
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


class Test(TestCommand):
    """Introduce test command to run testsuite using pytest."""

    _IMPLICIT_PYTEST_ARGS = [
        "--timeout=60",
        "--cov=./thoth",
        "--mypy",
        "--capture=no",
        "--verbose",
        "-l",
        "-s",
        "-vv",
        "--hypothesis-show-statistics",
        "tests/",
    ]

    user_options = [("pytest-args=", "a", "Arguments to pass into py.test")]

    def initialize_options(self):
        """Initialize cli options."""
        super().initialize_options()
        self.pytest_args = None

    def finalize_options(self):
        """Finalize cli options."""
        super().finalize_options()
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        """Run module tests."""
        import pytest

        passed_args = list(self._IMPLICIT_PYTEST_ARGS)

        if self.pytest_args:
            self.pytest_args = [arg for arg in self.pytest_args.split() if arg]
            passed_args.extend(self.pytest_args)

        sys.exit(pytest.main(passed_args))


VERSION = get_version()
setup(
    name="thoth-adviser",
    version=VERSION,
    description="Package and package stack adviser for the Thoth project",
    long_description=read("README.rst"),
    author="Fridolin Pokorny",
    author_email="fridolin@redhat.com",
    license="GPLv3+",
    packages=[
        "thoth.adviser",
        "thoth.adviser.boots",
        "thoth.adviser.predictors",
        "thoth.adviser.steps",
        "thoth.adviser.sieves",
        "thoth.adviser.sieves.backports",
        "thoth.adviser.strides",
        "thoth.adviser.wraps",
    ],
    url="https://github.com/thoth-station/adviser",
    download_url="https://pypi.org/project/thoth-adviser",
    package_data={"thoth.adviser": ["py.typed"]},
    entry_points={"console_scripts": ["thoth-adviser=thoth.adviser.cli:cli"]},
    zip_safe=False,
    install_requires=get_install_requires(),
    cmdclass={"test": Test},
    long_description_content_type="text/x-rst",
    command_options={"build_sphinx": {"version": ("setup.py", VERSION), "release": ("setup.py", VERSION),}},
)
