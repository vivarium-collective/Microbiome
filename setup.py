import os
import glob
import setuptools
from distutils.core import setup

with open("README.md", 'r') as readme:
    long_description = readme.read()

setup(
    name='vivarium-microbiome',  # TODO: Put your package name here.
    version='0.0.1',
    packages=[
        'vivarium_microbiome',
        'vivarium_microbiome.processes',
    ],
    author='Amin Boroomand',
    author_email='',  # TODO: Put your email here.
    url='',  # TODO: Put your project URL here.
    license='',  # TODO: Choose a license.
    entry_points={
        'console_scripts': []},
    short_description='',  # TODO: Describe your project briefely.
    long_description=long_description,
    long_description_content_type='text/markdown',
    package_data={},
    include_package_data=True,
    install_requires=[
        'vivarium-core>=1.0.0',
        'pytest',
        'cobra',
        # TODO: Add other dependencies.
    ],
)
