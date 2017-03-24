"""A setuptools based setup module for pylibofp.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup
# To use a consistent encoding
from codecs import open
from os import path
import re

here = path.abspath(path.dirname(__file__))
description_path = path.join(here, 'long_description.rst')
version_path = path.join(here, 'pylibofp', '__init__.py')

# Read long_description.rst.
with open(description_path, encoding='utf-8') as f:
    long_description = f.read()

# Extract version number.
with open(version_path, encoding='utf-8') as f:
    version_regex = re.compile(r"(?m)__version__\s*=\s*'(\d+\.\d+\.\d+)'")
    version = version_regex.search(f.read()).group(1)

# Running `python setup.py test` should run unit tests (see `test_suite`).
def _my_tests():
    import unittest
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests')
    return test_suite


setup(
    name='pylibofp',
    packages=['pylibofp'],
    version=version,
    license='MIT',

    description='OpenFlow App Framework',
    long_description=long_description,
    keywords='openflow controller mininet',

    # The project's main homepage and author.
    url='https://github.com/byllyfish/pylibofp',
    author='William W. Fisher',
    author_email='william.w.fisher@gmail.com',

    # Dependencies
    install_requires=[
        'prompt_toolkit'
    ],

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: System :: Networking'
    ],

    zip_safe=True,
    test_suite="setup._my_tests"
)