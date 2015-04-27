#!/usr/bin/env python3

from distutils.core import setup

setup(
    name='sentinel',
    version='0.1a',
    description='The sentinel framework.',
    author='Eric Johnson',
    author_email='eric.johnson@cs2.io',
    packages=[
        'sentinel',
        'sentinel.framework',
        'sentinel.apps',
        'sentinel.apps.console',
        'sentinel.apps.console.commands',
        'sentinel.user_services',
        'sentinel.team_services',
    ]
)
