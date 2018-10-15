# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path


here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

with open(path.join(here, 'requirements.txt')) as f:
    requirements = f.read().splitlines()

setup(
    name='sensortools',

    version='0.1.0',

    description='Python package containing functions for the Sensor data allotment GBDX Notebook.',
    long_description=long_description,

    author='Anthony Lopez',
    author_email='anthony.lopez@digitalglobe.com',

    classifiers=[
        'Development Status :: N/A'
        'Intended Audience :: Sales Engineers',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],

    packages=find_packages(['sensortools'], exclude=['tests', 'docs', 'examples']),

    install_requires=requirements

)
