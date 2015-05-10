import os
from importlib import import_module


class ServiceException(Exception):
    pass


class ServiceProvider:
    @property
    def name(self):
        raise NotImplementedError()

    @property
    def instance(self):
        raise NotImplementedError()


class SingletonServiceProvider(ServiceProvider):
    __instance = None
    __name = None

    def __init__(self, name, instance):
        self.__instance = instance
        self.__name = name

    @property
    def name(self):
        return self.__name

    @property
    def instance(self):
        return self.__instance


class LazyServiceProvider(ServiceProvider):
    __service_class = None
    __name = None
    __args = None
    __kwargs = None

    def __init__(self, name, service_class, *args, **kwargs):
        assert isinstance(name, str)
        assert isinstance(service_class, type)

        self.__service_class = service_class
        self.__name = name
        self.__args = args
        self.__kwargs = kwargs

    @property
    def args(self):
        return self.__args

    @property
    def kwargs(self):
        return self.__kwargs

    @property
    def name(self):
        return self.__name

    @property
    def service_class(self):
        return self.__service_class

    @property
    def instance(self):
        return self.__service_class(*self.__args, **self.__kwargs)


class LazySingletonServiceProvider(LazyServiceProvider):
    __instance = None

    @property
    def instance(self):
        if self.__instance is None:
            self.__instance = self.service_class(*self.args, **self.kwargs)
        return self.__instance


class LazyFactoryServiceProvider(LazyServiceProvider):
    @property
    def instance(self):
        return self.service_class(*self.args, **self.kwargs)


class ServiceManager:
    def __init__(self, parent=None):
        self.__providers = {}
        self.__parent = None
        self.parent = parent

    @property
    def parent(self):
        return self.__parent

    @parent.setter
    def parent(self, value):
        assert isinstance(value, ServiceManager) or value is None
        self.__parent = value

    def __getitem__(self, key):
        if key not in self.__providers:
            if self.__parent is not None:
                return self.__parent[key]
            raise ServiceException('No such service "{0}"'.format(key))
        return self.__providers[key].instance

    def __getattr__(self, key):
        if key in ['__providers', 'parent']:
            return object.__getattribute__(self, key)

        return self.__getitem__(key)

    def __hasattr__(self, key):
        if key not in self.__providers:
            if self.__parent is not None:
                return self.__parent.__hasattr__(key)
            return False
        return True

    def __setitem__(self, key, value):
        assert isinstance(value, ServiceProvider)
        if key in self.__providers:
            raise ServiceException('Service "{0}" already exists.'.format(key))
        self.__providers[key] = value

    def register(self, provider):
        assert isinstance(provider, ServiceProvider)
        self.__setitem__(provider.name, provider)


class ServiceUser:
    __service_manager = None

    @property
    def services(self):
        if ServiceUser.__service_manager is None:
            ServiceUser.__service_manager = ServiceManager()
            services_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'services')
            for fname in os.listdir(services_path):
                if fname in ['__init__.py', '__pycache__', '__main__.py']:
                    continue

                if os.path.isdir(os.path.join(services_path, fname)):
                    modname = fname
                else:
                    modname, extension = os.path.splitext(fname)
                    if extension != '.py':
                        continue

                module = import_module('...services.{0}'.format(modname), __name__)

                if not hasattr(module, 'provider'):
                    continue

                provider = getattr(module, 'provider')

                if not isinstance(provider, ServiceProvider):
                    continue

                ServiceUser.__service_manager.register(provider)

        return ServiceUser.__service_manager

    @services.setter
    def services(self, value):
        assert isinstance(value, ServiceManager)
        self.__service_manager = value


