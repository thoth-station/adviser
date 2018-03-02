import os
from setuptools import setup


def get_install_requires():
    with open('requirements.txt', 'r') as requirements_file:
        # TODO: respect hashes in requirements.txt file
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


setup(
    name='thoth-adviser',
    version=get_version(),
    description='Package and package stack adviser for the Thoth project',
    long_description='Package and package stack adviser for the Thoth project',
    author='Fridolin Pokorny',
    author_email='fridolin@redhat.com',
    license='GPLv2+',
    packages=[
        'thoth.adviser',
    ],
    entry_points={
        'console_scripts': ['thoth-adviser=thoth.adviser.cli:cli']
    },
    zip_safe=False,
    install_requires=get_install_requires()
)
