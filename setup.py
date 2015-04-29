#!/usr/bin/env python3

from distutils.core import setup
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import astra

setup(
    name='astra',
    version=astra.__version__,
    url='https://github.com/megamandos/astra',
    description='The Astra Exploit Framework',
    author='Eric Johnson',
    author_email='megamandos@gmail.com',
    packages=[
        'astra',
        'astra.framework',
        'astra.framework.router',
        'astra.apps',
        'astra.apps.teamserver',
        'astra.apps.console',
        'astra.apps.console.commands',
        'astra.services',
        'astra.components',
        'astra.components.console',
        'astra.test',
    ],
    package_data = {
        'astra.apps.teamserver': ['static/*']
    },
    requires=[
        'tornado',
        'sqlalchemy'
    ]
)
