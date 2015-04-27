#!/usr/bin/env python3
import sys
import os
from importlib import import_module
from argparse import ArgumentParser

# Determine the directory this file sits in.
astra_path = os.path.dirname(os.path.realpath(__file__))

# Determine what we are calling the astra package.
astra_pkg_name = os.path.basename(astra_path)

# Insert the directory above this into the path.
sys.path.insert(0, os.path.dirname(astra_path))

# Import the astra package
sys.modules['astra'] = import_module(astra_pkg_name)

# Get our argument parser.
parser = ArgumentParser()
subparsers = parser.add_subparsers()

# Get ready to load the application help data.
applications = {}
apps_directory = os.path.join(astra_path, 'apps')

for fname in os.listdir(apps_directory):
    if fname in ['__init__.py', '__main__.py', '__pycache__']:
        continue

    if os.path.isfile(os.path.join(apps_directory, fname)):
        module_name, extension = os.path.splitext(fname)
        if extension != '.py':
            continue
    else:
        module_name = fname

    class_name = '{0}Application'.format(''.join([word.capitalize() for word in  module_name.replace('_',' ').split()]))

    module = import_module('.apps.{0}'.format(module_name), 'astra')

    if not hasattr(module, class_name):
        raise Exception('Missing class "{0}" in app "{1}".'.format(class_name, module_name))

    app_class = getattr(module, class_name)

    subparser = subparsers.add_parser(module_name, help=app_class.__doc__)
    subparser.description = app_class.help.__doc__ if app_class.help.__doc__ != None else app_class.__doc__
    app_class.help(subparser)
    subparser.set_defaults(application=module_name)

    applications[module_name] = app_class

arguments = parser.parse_args()
if not hasattr(arguments, 'application'):
    parser.print_help()
    exit(0)

app_class = applications[arguments.application]
for argument,value in arguments.__dict__.items():
    setattr(app_class, argument, value)

app_class().run()
