#!/usr/bin/env python3

from setuptools import setup
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import astra

setup(
    name='astra',
    entry_points={
        'console_scripts': [
            'astra = astra:main'
        ]
    },
    version=astra.__version__,
    url='https://github.com/armalux/astra',
    description='The Astra Exploit Framework',
    author='Eric Johnson',
    author_email='eric.johnson@armalux.io',
    packages=[
        'astra',
        'astra.framework',
        'astra.framework.teamserver',
        'astra.apps',
        'astra.apps.teamserver',
        'astra.services',
        'astra.components',
        'astra.test',
    ],
    package_data={
        'astra.apps.teamserver': ['static/*']
    },
    requires=[
        'tornado'
    ]
)
