import os


class Callback:
    def __init__(self, function, *args, **kwargs):
        self.__function = function
        self.__args = args
        self.__kwargs = kwargs

    def run(self):
        return self.__function(*self.__args, **self.__kwargs)

    def call(self, *args, **kwargs):
        return self.__function(*args, **kwargs)

    def fork(self, *args, **kwargs):
        return Forker(self).fork(*args, **kwargs)

    def __mul__(self, number):
        assert isinstance(number, int)
        if number == 0:
            return []

        return [self for x in range(0, number)]


class Forker:
    def __init__(self, *callbacks):
        for callback in callbacks:
            assert isinstance(callback, Callback)

        self.__callbacks = callbacks

    def fork(self, daemonize=False, wait=True, exit_function=None):
        if exit_function is None:
            exit_function = exit

        pids = []
        for callback in self.__callbacks:
            pid = os.fork()
            if pid != 0:
                pids.append(pid)
                continue

            if daemonize:
                os.setsid()

            try:
                retval = callback.run()
                exit_function(retval)

            except Exception:
                exit(-1)

            finally:
                exit(0)

        if not daemonize and wait:
            for pid in pids:
                os.waitpid(pid, 0)

        return pids


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
