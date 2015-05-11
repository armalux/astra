__author__ = 'Eric Johnson'
__version__ = '0.1.dev2'
__all__ = ['framework', 'apps', 'services', 'components', 'test']


def main():
    import sys
    import os
    from importlib import import_module
    from argparse import ArgumentParser

    # Get our paths
    base_path = os.path.dirname(os.path.realpath(__file__))
    apps_path = os.path.join(base_path, 'apps')

    # Get our argument parser.
    parser = ArgumentParser()
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + sys.modules[__name__].__version__)
    subparsers = parser.add_subparsers()

    # Get ready to load the application help data.
    applications = {}

    for fname in os.listdir(apps_path):
        if fname in ['__init__.py', '__main__.py', '__pycache__']:
            continue

        if os.path.isfile(os.path.join(apps_path, fname)):
            module_name, extension = os.path.splitext(fname)
            if extension != '.py':
                continue
        else:
            module_name = fname

        class_name = '{0}Application'.format(''.join(
            [word.capitalize() for word in module_name.replace('_', ' ').split()]
        ))

        module = import_module('.apps.{0}'.format(module_name), 'astra')

        if not hasattr(module, class_name):
            raise Exception('Missing class "{0}" in app "{1}".'.format(class_name, module_name))

        app_class = getattr(module, class_name)


        desc = app_class.help.__doc__ if app_class.help.__doc__ is not None else app_class.__doc__
        subparser = subparsers.add_parser(module_name, help=desc)
        subparser.description = desc
        app_class.help(subparser)
        subparser.set_defaults(application=module_name)

        applications[module_name] = app_class

    arguments = parser.parse_args()
    if not hasattr(arguments, 'application'):
        parser.print_help()
        exit(0)

    app_class = applications[arguments.application]
    for argument, value in arguments.__dict__.items():
        setattr(app_class, argument, value)

    app_class().run()
