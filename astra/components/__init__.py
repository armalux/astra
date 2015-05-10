from importlib import import_module
import os
import sys
from ..framework.service import ServiceUser
from ..framework.teamserver.client import AstraClient


__all__ = []
_components = None


def load():
    global _components
    if _components is not None:
        return

    _components = []
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
            _components.append(attr)
            setattr(sys.modules[__name__], attr.__name__, attr)

    return _components


class Component(AstraClient, ServiceUser):
    def init(self):
        pass

    def on_client_connect(self, session_id):
        pass

    def on_client_disconnect(self, session_id):
        pass

    def on_client_subscribe(self, session_id, topic):
        pass

    def on_client_unsubscribe(self, session_id, topic):
        pass

    def on_client_register(self, session_id, procedure):
        pass

    def on_client_unregister(self, session_id, procedure):
        pass

    def on_client_call(self, session_id, procedure, *args, **kwargs):
        pass

    def on_client_publish(self, session_id, topic, *args, **kwargs):
        pass


