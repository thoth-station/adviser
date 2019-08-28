import os
import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand


def get_install_requires():
    with open('requirements.txt', 'r') as requirements_file:
        res = requirements_file.readlines()
        return [req.split(' ', maxsplit=1)[0] for req in res if req]


def get_version():
    with open(os.path.join('thoth', 'adviser', '__init__.py')) as f:
        content = f.readlines()

    for line in content:
        if line.startswith('__version__ ='):
            # dirty, remove trailing and leading chars
            return line.split(' = ')[1][1:-2]
    raise ValueError("No version identifier found")


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


class Test(TestCommand):
    """Introduce test command to run testsuite using pytest."""

    _IMPLICIT_PYTEST_ARGS = ['tests/', '--timeout=2', '--cov=./thoth', '--capture=no', '--verbose', '-l', '-s', '-vv']

    user_options = [
        ('pytest-args=', 'a', "Arguments to pass into py.test")
    ]

    def initialize_options(self):
        super().initialize_options()
        self.pytest_args = None

    def finalize_options(self):
        super().finalize_options()
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        passed_args = list(self._IMPLICIT_PYTEST_ARGS)

        if self.pytest_args:
            self.pytest_args = [arg for arg in self.pytest_args.split() if arg]
            passed_args.extend(self.pytest_args)

        sys.exit(pytest.main(passed_args))


VERSION = get_version()
setup(
    name='thoth-adviser',
    version=VERSION,
    description='Package and package stack adviser for the Thoth project',
    long_description=read('README.rst'),
    author='Fridolin Pokorny',
    author_email='fridolin@redhat.com',
    license='GPLv3+',
    packages=[
        'thoth.adviser',
        'thoth.adviser.python',
        'thoth.adviser.python.pipeline',
        'thoth.adviser.python.dependency_graph',
        'thoth.adviser.python.pipeline.steps',
        'thoth.adviser.python.pipeline.units',
        'thoth.adviser.python.pipeline.sieves',
        'thoth.adviser.python.pipeline.strides',
        'thoth.adviser.python.dependency_graph.walking',
        'thoth.adviser.python.dependency_graph.adaptation',
    ],
    entry_points={
        'console_scripts': ['thoth-adviser=thoth.adviser.cli:cli']
    },
    zip_safe=False,
    install_requires=get_install_requires(),
    cmdclass={'test': Test},
    command_options={
        'build_sphinx': {
            'version': ('setup.py', VERSION),
            'release': ('setup.py', VERSION),
        }
    }
)
