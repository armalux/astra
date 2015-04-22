
class ServiceException(Exception):
    pass


class ServiceProvider:
    @property
    def name(self):
        raise NotImplementedError()

    @property
    def instance(self):
        raise NotImplementedError()


class SimpleServiceProvider(ServiceProvider):
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


class SingletonServiceProvider(SimpleServiceProvider):
    __instance = None

    @property
    def instance(self):
        if self.__instance is None:
            self.__instance = self.service_class(*self.args, **self.kwargs)
        return self.__instance


class FactoryServiceProvider(SimpleServiceProvider):
    @property
    def instance(self):
        return self.service_class(*self.args, **self.kwargs)


class ServiceManager:
    def __init__(self):
        self.__providers = {}

    def __getitem__(self, key):
        if key not in self.__providers:
            raise ServiceException('No such service "{0}"'.format(key))
        return self.__providers[key].instance

    def __getattr__(self, key):
        if key == '__providers':
            return object.__getattribute__(self, '__providers')

        return self.__getitem__(key)

    def __setitem__(self, key, value):
        assert isinstance(value, ServiceProvider)
        if key in self.__providers:
            raise ServiceException('Service "{0}" already exists.'.format(key))
        self.__providers[key] = value

    def register(self, provider):
        assert isinstance(provider, ServiceProvider)
        self.__setitem__(provider.name, provider)


class ServiceUser:
    __services = None

    @property
    def services(self):
        if self.__services is None:
            self.__services = ServiceManager()
        return self.__services

    @services.setter
    def services(self, value):
        assert isinstance(value, ServiceManager)
        self.__services = value


class Application(ServiceUser):

    @staticmethod
    def help(parser):
        raise NotImplementedError()

    def run(self):
        raise NotImplementedError()
