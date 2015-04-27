#!/usr/bin/env python3

from distutils.core import setup

setup(
    name='astra',
    version='0.1a',
    description='The astra framework.',
    author='Eric Johnson',
    author_email='megamandos@gmail.com',
    packages=[
        'astra',
        'astra.framework',
        'astra.apps',
        'astra.apps.console',
        'astra.apps.console.commands',
        'astra.user_services',
        'astra.team_services',
    ]
)
