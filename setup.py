import os
import glob
import setuptools
from distutils.core import setup

with open("README.md", 'r') as readme:
    long_description = readme.read()

setup(
    name='vivarium-microbiome',
    version='0.0.1',
    packages=[
        'vivarium_microbiome',
        'vivarium_microbiome.processes',
    ],
    author='Amin Boroomand',
    author_email='boroomand@uchc.edu',
    url='',  # TODO: Put your project URL here.
    license='Apache 2',
    entry_points={
        'console_scripts': []},
    short_description='',  # TODO: Describe your project briefly.
    long_description=long_description,
    long_description_content_type='text/markdown',
    package_data={},
    include_package_data=True,
    install_requires=[
        'vivarium-core>=1.0.0',
        'pytest',
        'cobra',
    ],
)
