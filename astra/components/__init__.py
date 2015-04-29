from ..framework.router import Component
from importlib import import_module
import os
import inspect
import sys


__all__ = []
components = []


this_path = os.path.dirname(os.path.realpath(__file__))
for fname in os.listdir(this_path):
    if fname in ['__pycache__', '__init__.py', '__main__.py']:
        continue

    if os.path.isdir(os.path.join(this_path, fname)):
        modname = fname
    else:
        modname, extension = os.path.splitext(fname)
        if extension != '.py':
            continue

    module = import_module('.{0}'.format(modname), __name__)
    for attr in module.__dict__.values():
        if not isinstance(attr, type):
            continue

        if attr is Component:
            continue

        if Component not in attr.__bases__:
            continue

        __all__.append(attr.__name__)
        components.append(attr)
        setattr(sys.modules[__name__], attr.__name__, attr)



