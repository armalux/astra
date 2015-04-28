from ..framework.service import SingletonServiceProvider
from ..framework.singleton import Singleton
import threading


class UserService(Singleton):
    __provider__ = SingletonServiceProvider('user', UserService())
    _thread_storage = threading.local()

    @property
    def storage(self):
        return self._thread_storage.storage

    @property
    def connection(self):
        return self._thread_storage.connection
