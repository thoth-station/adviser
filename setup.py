from setuptools import setup


def get_install_requires():
    with open('requirements.txt', 'r') as requirements_file:
        # TODO: respect hashes in requirements.txt file
        res = requirements_file.readlines()
        return [req.split(' ', maxsplit=1)[0] for req in res if req]


setup(
    name='thoth-advisor',
    version='0.0.0',
    description='Package and package stack advisor for the Thoth project',
    long_description='Package and package stack advisor for the Thoth project',
    author='Fridolin Pokorny',
    author_email='fridolin@redhat.com',
    license='GPLv2+',
    packages=[
        'thoth.advisor',
    ],
    zip_safe=False,
    install_requires=get_install_requires()
)
