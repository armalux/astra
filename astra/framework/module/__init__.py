__author__ = 'Eric Johnson'
from ..service import ServiceUser
from ..singleton import Singleton
from ..console import ConsoleCommand
import os


class AstraComponent(ServiceUser):
    name = None
    description = None


class CommandComponent(AstraComponent, ConsoleCommand):
    def run(self):
        raise NotImplementedError()


component_types = {
    'command': CommandComponent,
}


class ModuleManager(Singleton):
    def __init__(self):
        self._directories = set()
        self._files = set()
        self._modules = {}
        self._components = {}

    @property
    def components(self):
        return self._components

    @property
    def modules(self):
        return self._modules

    def add_directory(self, path):
        path = os.path.realpath(path)
        assert os.path.isdir(path)
        self._directories.add(path)

    def load(self):
        components = {name: {} for name in component_types.keys()}
        modules = {}

        for directory in self._directories:
            for module in ModuleLoader.load_directory(directory):
                modules[module.uri] = module

        for file_path in self._files:
            module = ModuleLoader.load(file_path)
            modules[module.uri] = module

        for module in modules.values():
            for type_name in component_types.keys():
                for name, value in module.components[type_name].items():
                    components[type_name][name] = value

        self._components = components
        self._modules = modules


class ModuleLoader:
    @classmethod
    def load_module(cls, contents, filename=None, package=None):
        if filename is None:
            filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ext_module.py')

        if package is None:
            package = 'astra.framework.module'

        dct = {'__file__': filename,
               '__package__': package,
               '__loader__': cls}
        code = compile(contents, filename, 'exec')
        exec(code, dct)

        required_attributes = ['author', 'uri', 'name', 'description']
        for attr in required_attributes:
            if attr not in dct:
                raise ImportError('Module missing required attribute: {0}'.format(attr))

        return AstraModule(dct['author'], dct['name'], dct['uri'], dct['description'], filename,
                           cls.find_components(dct))

    @classmethod
    def load(cls, path):
        path = os.path.realpath(path)
        assert os.path.isfile(path)
        with open(path) as f:
            return cls.load_module(f.read(), path)

    @staticmethod
    def find_components(dct):
        """
        Search through dct to find components that we can use.
        :param dct: a dictionary containing attributes from a module
        :return: a dictionary containing the components found
        """

        components = {name: {} for name in component_types.keys()}

        for name, value in dct.items():
            if not isinstance(value, type):
                continue

            for type_name, type_class in component_types.items():
                if not issubclass(value, type_class):
                    continue

                if value is type_class:
                    continue

                break

            else:
                continue

            # noinspection PyUnresolvedReferences
            components[type_name][value.name] = value

        return components

    @classmethod
    def load_directory(cls, path):
        path = os.path.realpath(path)
        assert os.path.isdir(path)

        modules = []
        for fname in os.listdir(path):
            if fname in ['__pycache__', '__init__.py', '__main__.py']:
                continue

            fullpath = os.path.join(path, fname)
            if os.path.isdir(fullpath):
                modules += cls.load_directory(fullpath)
                continue

            modules.append(cls.load(fullpath))

        return modules


class AstraModule(ServiceUser):
    author = None
    uri = None
    name = None
    description = None
    components = None

    def __init__(self, author, name, uri, description, path, components):
        self.author = author
        self.name = name
        self.path = path
        self.uri = uri
        self.description = description
        self.components = components
